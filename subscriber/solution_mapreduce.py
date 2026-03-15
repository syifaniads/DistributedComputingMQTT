import json
import os
from collections import defaultdict
import paho.mqtt.client as mqtt

BROKER_HOST = os.environ.get("MQTT_BROKER", "10.34.100.103")
BROKER_PORT = int(os.environ.get("MQTT_PORT", 1883))
TOPIC = "stasiun/cuaca/#"
BATCH_SIZE = 20

buffer = []
batch_no = 1


def kategori_aqi(aqi):
    if aqi <= 50:
        return "Baik"
    elif aqi <= 100:
        return "Sedang"
    elif aqi <= 150:
        return "Tidak Sehat (sensitif)"
    elif aqi <= 200:
        return "Tidak Sehat"
    else:
        return "Sangat Tidak Sehat"


def process_batch(data):

    global batch_no

    print("\n════════════════════════════════════════════")
    print(f"[MapReduce] Batch #{batch_no} ({len(data)} record)")
    print("════════════════════════════════════════════")

    # MAP
    mapped = []

    for d in data:
        mapped.append(
            (
                d["station_id"],
                {
                    "suhu": d["suhu_c"],
                    "kelembaban": d["kelembaban_pct"],
                    "aqi": d["aqi"],
                    "hujan": d["curah_hujan_mm"],
                    "angin": d["kecepatan_angin"],
                },
            )
        )

    # SHUFFLE
    grouped = defaultdict(list)

    for key, value in mapped:
        grouped[key].append(value)

    print(
        "Stasiun  Count  SuhuAvg  SuhuMax  AQIavg  AQImax  HujanTotal  StatusUdara"
    )

    # REDUCE
    for station, values in grouped.items():

        count = len(values)
        suhu = [v["suhu"] for v in values]
        aqi = [v["aqi"] for v in values]
        hujan = [v["hujan"] for v in values]
        lembab = [v["kelembaban"] for v in values]

        suhu_avg = sum(suhu) / count
        suhu_max = max(suhu)

        aqi_avg = sum(aqi) / count
        aqi_max = max(aqi)

        hujan_total = sum(hujan)

        status = kategori_aqi(aqi_avg)

        print(
            f"{station:7} {count:5} {suhu_avg:7.2f} {suhu_max:7.2f} {aqi_avg:7.2f} {aqi_max:7} {hujan_total:10.2f} {status}"
        )

    batch_no += 1


def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected to broker")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):

    try:
        payload = json.loads(msg.payload.decode())

        buffer.append(payload)

        if len(buffer) >= BATCH_SIZE:
            process_batch(buffer.copy())
            buffer.clear()

    except Exception as e:
        print("Error:", e)


client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_HOST, BROKER_PORT, 60)

client.loop_forever()
