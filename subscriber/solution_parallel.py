import json
import os
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import paho.mqtt.client as mqtt

BROKER_HOST = os.environ.get("MQTT_BROKER", "10.34.100.103")
BROKER_PORT = int(os.environ.get("MQTT_PORT", 1883))
TOPIC = "stasiun/cuaca/#"

NUM_WORKERS = 4
REPORT_EVERY = 10

lock = threading.Lock()

suhu_stats = defaultdict(lambda: {"n": 0, "total": 0, "min": 999, "max": -999})
aqi_kategori = defaultdict(int)
ekstrem = defaultdict(int)

event_count = 0

executor = ThreadPoolExecutor(max_workers=NUM_WORKERS)


def kategori_aqi(aqi):

    if aqi <= 50:
        return "Baik"
    elif aqi <= 100:
        return "Sedang"
    elif aqi <= 150:
        return "Sensitif"
    elif aqi <= 200:
        return "Tidak Sehat"
    else:
        return "Sangat Tidak Sehat"


def worker_statistik_suhu(d):

    with lock:
        s = suhu_stats[d["station_id"]]

        s["n"] += 1
        s["total"] += d["suhu_c"]

        s["min"] = min(s["min"], d["suhu_c"])
        s["max"] = max(s["max"], d["suhu_c"])


def worker_kualitas_udara(d):

    k = kategori_aqi(d["aqi"])

    with lock:
        aqi_kategori[k] += 1


def worker_cuaca_ekstrem(d):

    if d["suhu_c"] > 38 or d["aqi"] > 150 or d["kecepatan_angin"] > 40:

        with lock:
            ekstrem[d["station_id"]] += 1


def worker_agregat_global(d):
    pass


def print_report():

    print("\n=== RINGKASAN GLOBAL ===")

    for sid, s in suhu_stats.items():

        avg = s["total"] / s["n"]

        print(
            f"{sid} avg={avg:.2f} min={s['min']:.2f} max={s['max']:.2f}"
        )

    print("\nDistribusi AQI")

    for k, v in aqi_kategori.items():
        print(k, v)

    print("\nEvent ekstrem")

    for sid, v in ekstrem.items():
        print(sid, v)


def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected to broker")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):

    global event_count

    try:
        d = json.loads(msg.payload.decode())

        futures = [
            executor.submit(worker_statistik_suhu, d),
            executor.submit(worker_kualitas_udara, d),
            executor.submit(worker_cuaca_ekstrem, d),
            executor.submit(worker_agregat_global, d),
        ]

        for f in as_completed(futures):
            f.result()

        event_count += 1

        if event_count % REPORT_EVERY == 0:
            print_report()

    except Exception as e:
        print("Error:", e)


client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_HOST, BROKER_PORT, 60)

client.loop_forever()
