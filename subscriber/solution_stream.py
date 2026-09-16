import json
import os

import paho.mqtt.client as mqtt

from subscriber.weather_processing import WindowProcessor

BROKER_HOST = os.environ.get("MQTT_BROKER", "localhost")
BROKER_PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC = os.environ.get("MQTT_TOPIC", "stasiun/cuaca/#")
WINDOW_SIZE = int(os.environ.get("TUMBLE_SIZE", "10"))
SLIDE_SIZE = int(os.environ.get("SLIDE_SIZE", "5"))
processor = WindowProcessor(slide_size=SLIDE_SIZE, tumble_size=WINDOW_SIZE)
event_id = 1


def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"connected to {BROKER_HOST}:{BROKER_PORT}")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    global event_id
    try:
        event = json.loads(msg.payload.decode("utf-8"))
        result = processor.process(event)
        print(
            f"[Stream #{event_id:4}] {result['station_id']} "
            f"slide_n={result['sliding_count']} "
            f"avg_temp={result['sliding_temperature_avg']:.2f} "
            f"avg_aqi={result['sliding_aqi_avg']:.2f}"
        )
        if result["alerts"]:
            print(" ALERT:", ", ".join(result["alerts"]))
        if result["tumbling"] is not None:
            print(" TUMBLING:", result["tumbling"])
        event_id += 1
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
