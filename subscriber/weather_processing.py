from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

REQUIRED_FIELDS = {
    "station_id",
    "suhu_c",
    "kelembaban_pct",
    "aqi",
    "curah_hujan_mm",
    "kecepatan_angin",
}


def validate_event(event: dict[str, Any]) -> dict[str, Any]:
    missing = REQUIRED_FIELDS.difference(event)
    if missing:
        raise ValueError(f"missing weather fields: {', '.join(sorted(missing))}")
    if not str(event["station_id"]).strip():
        raise ValueError("station_id must not be empty")
    for field_name in REQUIRED_FIELDS - {"station_id"}:
        if not isinstance(event[field_name], (int, float)):
            raise ValueError(f"{field_name} must be numeric")
    return event


def aqi_category(aqi: float) -> str:
    if aqi <= 50:
        return "Baik"
    if aqi <= 100:
        return "Sedang"
    if aqi <= 150:
        return "Tidak Sehat (sensitif)"
    if aqi <= 200:
        return "Tidak Sehat"
    return "Sangat Tidak Sehat"


def aggregate_batch(events: list[dict[str, Any]]) -> dict[str, dict[str, float | int | str]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw in events:
        event = validate_event(raw)
        grouped[str(event["station_id"])].append(event)

    output: dict[str, dict[str, float | int | str]] = {}
    for station_id, values in grouped.items():
        temperatures = [float(v["suhu_c"]) for v in values]
        aqis = [float(v["aqi"]) for v in values]
        rain = [float(v["curah_hujan_mm"]) for v in values]
        output[station_id] = {
            "count": len(values),
            "temperature_avg": sum(temperatures) / len(values),
            "temperature_max": max(temperatures),
            "aqi_avg": sum(aqis) / len(values),
            "aqi_max": max(aqis),
            "rain_total": sum(rain),
            "air_status": aqi_category(sum(aqis) / len(values)),
        }
    return output


def alerts_for(event: dict[str, Any]) -> list[str]:
    event = validate_event(event)
    alerts: list[str] = []
    if event["suhu_c"] > 38:
        alerts.append("SUHU TINGGI")
    if event["aqi"] > 150:
        alerts.append("AQI TIDAK SEHAT")
    if event["kecepatan_angin"] > 40:
        alerts.append("ANGIN KENCANG")
    if event["curah_hujan_mm"] > 5:
        alerts.append("HUJAN LEBAT")
    return alerts


@dataclass
class WindowProcessor:
    slide_size: int = 5
    tumble_size: int = 10
    sliding: dict[str, deque] = field(default_factory=lambda: defaultdict(deque))
    tumbling: dict[str, list] = field(default_factory=lambda: defaultdict(list))

    def __post_init__(self) -> None:
        if self.slide_size <= 0 or self.tumble_size <= 0:
            raise ValueError("window sizes must be positive")

    def process(self, raw: dict[str, Any]) -> dict[str, Any]:
        event = validate_event(raw)
        station_id = str(event["station_id"])

        if station_id not in self.sliding or self.sliding[station_id].maxlen != self.slide_size:
            self.sliding[station_id] = deque(maxlen=self.slide_size)
        self.sliding[station_id].append(event)
        self.tumbling[station_id].append(event)

        slide = list(self.sliding[station_id])
        result: dict[str, Any] = {
            "station_id": station_id,
            "alerts": alerts_for(event),
            "sliding_count": len(slide),
            "sliding_temperature_avg": sum(float(x["suhu_c"]) for x in slide) / len(slide),
            "sliding_aqi_avg": sum(float(x["aqi"]) for x in slide) / len(slide),
            "tumbling": None,
        }

        if len(self.tumbling[station_id]) >= self.tumble_size:
            batch = self.tumbling[station_id][: self.tumble_size]
            del self.tumbling[station_id][: self.tumble_size]
            result["tumbling"] = aggregate_batch(batch)[station_id]

        return result
