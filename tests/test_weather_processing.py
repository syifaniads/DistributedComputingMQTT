import pytest

from subscriber.weather_processing import WindowProcessor, aggregate_batch, alerts_for, aqi_category, validate_event


def event(station="WS-001", temp=30.0, aqi=80, rain=0.0, wind=10.0):
    return {
        "station_id": station,
        "lokasi": "Lab",
        "suhu_c": temp,
        "kelembaban_pct": 70.0,
        "aqi": aqi,
        "curah_hujan_mm": rain,
        "kecepatan_angin": wind,
        "arah_angin": "N",
    }


def test_schema_validation_rejects_missing_field():
    bad = event()
    del bad["aqi"]
    with pytest.raises(ValueError):
        validate_event(bad)


def test_aqi_boundaries():
    assert aqi_category(50) == "Baik"
    assert aqi_category(100) == "Sedang"
    assert aqi_category(150) == "Tidak Sehat (sensitif)"
    assert aqi_category(200) == "Tidak Sehat"
    assert aqi_category(201) == "Sangat Tidak Sehat"


def test_batch_aggregation_is_partitioned_by_station():
    result = aggregate_batch([
        event("WS-001", temp=20, aqi=50, rain=1),
        event("WS-001", temp=30, aqi=100, rain=2),
        event("WS-002", temp=40, aqi=200, rain=3),
    ])
    assert result["WS-001"]["count"] == 2
    assert result["WS-001"]["temperature_avg"] == 25
    assert result["WS-001"]["rain_total"] == 3
    assert result["WS-002"]["count"] == 1


def test_sliding_state_is_isolated_per_station():
    processor = WindowProcessor(slide_size=2, tumble_size=3)
    processor.process(event("A", temp=10))
    processor.process(event("B", temp=100))
    result = processor.process(event("A", temp=20))
    assert result["sliding_count"] == 2
    assert result["sliding_temperature_avg"] == 15


def test_tumbling_window_emits_and_resets():
    processor = WindowProcessor(slide_size=2, tumble_size=2)
    assert processor.process(event("A", temp=10))["tumbling"] is None
    emitted = processor.process(event("A", temp=20))["tumbling"]
    assert emitted["count"] == 2
    assert emitted["temperature_avg"] == 15
    assert processor.process(event("A", temp=30))["tumbling"] is None


def test_alerts_cover_multiple_conditions():
    result = alerts_for(event(temp=39, aqi=151, rain=6, wind=41))
    assert set(result) == {"SUHU TINGGI", "AQI TIDAK SEHAT", "HUJAN LEBAT", "ANGIN KENCANG"}
