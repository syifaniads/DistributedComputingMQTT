import json
import os
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import paho.mqtt.client as mqtt

from subscriber.weather_processing import aqi_category, alerts_for, validate_event

BROKER_HOST = os.environ.get("MQTT_BROKER", "localhost")
BROKER_PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC = os.environ.get("MQTT_TOPIC", "stasiun/cuaca/#")
NUM_WORKERS = int(os.environ.get("NUM_WORKERS", "4"))
REPORT_EVERY = int(os.environ.get("REPORT_EVERY", "10"))

lock = threading.Lock()
temperature_stats = defaultdict(lambda: {"n": 0, "total": 0.0, "min": float("inf"), "max": float("-inf")})
aqi_categories = defaultdict(int)
extreme_events = defaultdict(int)
event_count = 0
executor = ThreadPoolExecutor(max_workers=NUM_WORKERS)


def temperature_result(event):
    return event["station_id"], float(event["suhu_c"])


def air_result(event):
    return aqi_category(float(event["aqi"]))


def extreme_result(event):
    return event["station_id"], bool(alerts_for(event))


def merge_results(temp, air, extreme):
    station_id, temperature = temp
    extreme_station, is_extreme = extreme
    with lock:
        stats = temperature_stats[station_id]
        stats["n"] += 1
        stats["total"] += temperature
        stats["min"] = min(stats["min"], temperature)
        stats["max"] = max(stats["max"], temperature)
        aqi_categories[air] += 1
        if is_extreme:
            extreme_events[extreme_station] += 1


def print_report():
    with lock:
        print("\n=== GLOBAL SUMMARY ===")
        for station_id, stats in sorted(temperature_stats.items()):
            average = stats["total"] / stats["n"]
            print(f"{station_id} avg={average:.2f} min={stats['min']:.2f} max={stats['max']:.2f}")
        print("AQI categories:", dict(aqi_categories))
        print("Extreme events:", dict(extreme_events))


def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"connected to {BROKER_HOST}:{BROKER_PORT}")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    global event_count
    try:
        event = validate_event(json.loads(msg.payload.decode("utf-8")))
        future_temp = executor.submit(temperature_result, event)
        future_air = executor.submit(air_result, event)
        future_extreme = executor.submit(extreme_result, event)
        merge_results(future_temp.result(), future_air.result(), future_extreme.result())
        event_count += 1
        if event_count % REPORT_EVERY == 0:
            print_report()
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print("discarded invalid event:", exc)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    try:
        client.loop_forever()
    finally:
        executor.shutdown(wait=True)


if __name__ == "__main__":
    main()
