import json
import os
from collections import defaultdict, deque
import paho.mqtt.client as mqtt

BROKER_HOST = os.environ.get("MQTT_BROKER", "10.34.100.103")
BROKER_PORT = int(os.environ.get("MQTT_PORT", 1883))
TOPIC = "stasiun/cuaca/#"

WINDOW_SIZE = 10
SLIDE_SIZE = 5

ALERT_SUHU_MAX = 38
ALERT_AQI_MAX = 150
ALERT_ANGIN_MAX = 40
ALERT_HUJAN_MIN = 5

sliding = defaultdict(lambda: deque(maxlen=SLIDE_SIZE))
tumbling = defaultdict(list)

event_id = 1


def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected to broker")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):

    global event_id

    try:
        d = json.loads(msg.payload.decode())

        sid = d["station_id"]

        print(
            f"[Stream #{event_id:4}] {sid} {d['lokasi']} | suhu={d['suhu_c']}C aqi={d['aqi']} angin={d['kecepatan_angin']} hujan={d['curah_hujan_mm']}"
        )

        alerts = []

        if d["suhu_c"] > ALERT_SUHU_MAX:
            alerts.append("SUHU TINGGI")

        if d["aqi"] > ALERT_AQI_MAX:
            alerts.append("AQI TIDAK SEHAT")

        if d["kecepatan_angin"] > ALERT_ANGIN_MAX:
            alerts.append("ANGIN KENCANG")

        if d["curah_hujan_mm"] > ALERT_HUJAN_MIN:
            alerts.append("HUJAN LEBAT")

        if alerts:
            print(" ALERT:", ", ".join(alerts))

        # sliding window
        sliding[sid].append(d)

        if len(sliding[sid]) >= 2:

            avg_suhu = sum(x["suhu_c"] for x in sliding[sid]) / len(sliding[sid])
            avg_aqi = sum(x["aqi"] for x in sliding[sid]) / len(sliding[sid])

            print(
                f" sliding[{sid}] avg_suhu={avg_suhu:.2f} avg_aqi={avg_aqi:.2f}"
            )

        # tumbling window
        tumbling[sid].append(d)

        if len(tumbling[sid]) >= WINDOW_SIZE:

            data = tumbling[sid]

            avg_suhu = sum(x["suhu_c"] for x in data) / len(data)
            max_suhu = max(x["suhu_c"] for x in data)

            avg_aqi = sum(x["aqi"] for x in data) / len(data)
            max_aqi = max(x["aqi"] for x in data)

            print("\nTUMBLING WINDOW", sid)
            print("avg_suhu:", avg_suhu)
            print("max_suhu:", max_suhu)
            print("avg_aqi:", avg_aqi)
            print("max_aqi:", max_aqi)

            tumbling[sid].clear()

        event_id += 1

    except Exception as e:
        print("Error:", e)


client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_HOST, BROKER_PORT, 60)

client.loop_forever()
