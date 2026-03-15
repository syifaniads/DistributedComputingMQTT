import json
import os
import paho.mqtt.client as mqtt

BROKER_HOST = os.environ.get("MQTT_BROKER", "10.34.100.103")
BROKER_PORT = int(os.environ.get("MQTT_PORT", 1883))
TOPIC = "stasiun/cuaca/#"

def on_connect(client, userdata, flags, rc):
    print("Connected to broker")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(payload)
    except Exception as e:
        print("Error:", e)

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_HOST, BROKER_PORT)

client.loop_forever()
