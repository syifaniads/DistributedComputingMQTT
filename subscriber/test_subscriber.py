import json
import os

import paho.mqtt.client as mqtt

from subscriber.weather_processing import validate_event

BROKER_HOST = os.environ.get("MQTT_BROKER", "localhost")
BROKER_PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC = os.environ.get("MQTT_TOPIC", "stasiun/cuaca/#")


def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"connected to {BROKER_HOST}:{BROKER_PORT}")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = validate_event(json.loads(msg.payload.decode("utf-8")))
        print(payload)
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
