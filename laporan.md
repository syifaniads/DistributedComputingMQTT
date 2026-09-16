# Laporan Praktikum Sistem Komputasi Terdistribusi — Sanitized Summary

## Studi Kasus: Sistem Pemantauan Stasiun Cuaca Cerdas

**Mahasiswa:** Syifani Adillah Salsabila  
**Mata kuliah:** Sistem Komputasi Terdistribusi

> Portfolio note: the original coursework report contained a student identifier and lab-specific environment details. This public version keeps the technical findings while removing identifying infrastructure/academic identifiers. The original Git history remains the historical record.

## A. Batch MapReduce

The retained lab used `BATCH_SIZE = 20`. With the report's publisher workload of about 5 events/s (one event from each of five stations), a batch fills in roughly 4 seconds. Increasing the count to 100 produces an estimated fill time of roughly 20 seconds. The report uses this to explain the trade-off between larger sample sets and delayed output.

Events enter the buffer in MQTT arrival order. The Map stage emits `(station_id, measurements)` pairs; Shuffle groups those pairs by station; Reduce computes per-station statistics such as temperature average/max, AQI average/max, and rainfall total.

The report also considers changing the key from `station_id` to `arah_angin`. That would shift the analytical question from per-station conditions toward associations between wind direction and AQI, rainfall, and wind-speed patterns. Those associations would still require careful interpretation rather than causal claims.

## B. Stream processing

Per-station state is stored separately so observations from different stations do not contaminate one another. A sliding window summarizes recent station observations, while a tumbling window emits a summary after a fixed number of events.

The retained exercise also generates alerts for conditions such as high temperature, unhealthy AQI, strong wind, and heavy rainfall. The report observed frequent alerts in specific station streams during the lab run, but those generated/simulated observations should not be generalized to real environmental conditions.

## C. Parallel processing

The parallel variant distributes independent analytic functions to a `ThreadPoolExecutor` and protects shared aggregate state with a lock. The assignment demonstrates synchronization and fan-out/fan-in mechanics. It does not establish that the threaded version is faster; the portfolio engineering review explicitly calls for measurement because the workload is small and Python threading has scheduling/GIL/lock overhead.

## Portfolio interpretation

The educational value of the exercise is the comparison of processing semantics on one event stream:

- batch size affects output cadence;
- partitioning state by key affects correctness;
- stream windows introduce state lifecycle questions;
- concurrency introduces synchronization/throughput trade-offs;
- real distributed systems additionally need delivery semantics, backpressure, durable state, observability, and failure recovery.
