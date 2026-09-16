import json
import os

import paho.mqtt.client as mqtt

from subscriber.weather_processing import aggregate_batch

BROKER_HOST = os.environ.get("MQTT_BROKER", "localhost")
BROKER_PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC = os.environ.get("MQTT_TOPIC", "stasiun/cuaca/#")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "20"))

buffer = []
batch_no = 1


def process_batch(data):
    global batch_no
    results = aggregate_batch(data)
    print(f"\n[MapReduce] Batch #{batch_no} ({len(data)} records)")
    print("station count temp_avg temp_max aqi_avg aqi_max rain_total status")
    for station, stats in sorted(results.items()):
        print(
            f"{station:7} {stats['count']:5} "
            f"{stats['temperature_avg']:8.2f} {stats['temperature_max']:8.2f} "
            f"{stats['aqi_avg']:7.2f} {stats['aqi_max']:7.0f} "
            f"{stats['rain_total']:10.2f} {stats['air_status']}"
        )
    batch_no += 1


def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"connected to {BROKER_HOST}:{BROKER_PORT}")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        buffer.append(payload)
        if len(buffer) >= BATCH_SIZE:
            process_batch(buffer[:BATCH_SIZE])
            del buffer[:BATCH_SIZE]
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print("discarded invalid event:", exc)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
