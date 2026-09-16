# Production gaps

A production weather-telemetry pipeline would need decisions and tests for:

- MQTT QoS, persistent sessions, reconnect and retained-message policy;
- TLS and broker authentication/authorization;
- message IDs, deduplication and idempotent consumers;
- schema registry/versioning and invalid-event dead-letter handling;
- bounded buffers, queue depth metrics and backpressure;
- event-time vs processing-time semantics;
- late and out-of-order events;
- durable state/checkpointing/replay;
- partition ownership when horizontally scaled;
- broker/consumer failure drills;
- p50/p95/p99 end-to-end latency and sustainable throughput;
- logs, metrics and tracing for message rate, processing time, queue depth and errors.

The current repo is intentionally a compact coursework lab rather than claiming those capabilities are implemented.
