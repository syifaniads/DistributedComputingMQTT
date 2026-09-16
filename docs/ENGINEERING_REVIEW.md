# Engineering review

## What the coursework demonstrates well

The lab makes three different computation models concrete on the same MQTT event stream: batch MapReduce, per-key stateful windows, and thread-pool fan-out. That makes latency/state/concurrency trade-offs visible without requiring a large framework.

## Important technical boundaries

### MapReduce is local, not distributed MapReduce

The Map/Shuffle/Reduce stages are implemented inside one Python process. The algorithmic pattern is useful, but there is no distributed scheduler, worker partitioning, data locality, shuffle network, retry model, or durable intermediate storage comparable to Hadoop/Spark.

### Windows are count-based

The sliding/tumbling windows count events per station. They are not event-time windows and do not implement watermarks, allowed lateness, or out-of-order handling.

### ThreadPoolExecutor is not a throughput guarantee

The parallel variant fans three small analytic functions out to Python threads and waits for each result before finishing the MQTT callback. For tiny CPU-bound functions, task scheduling, GIL serialization, and locking can make this slower than sequential code. A useful experiment would benchmark sequential vs threaded variants at increasing event rates instead of assuming parallelism is faster.

### State and failure handling

All state is in process memory. A restart loses batch buffers, windows, and cumulative counters. Production stream systems need durable state/checkpoints or a deliberate replay strategy.

### Delivery semantics

The coursework does not establish idempotency or deduplication. With MQTT QoS/reconnect behavior, a production consumer needs a message identity strategy if duplicate processing has side effects.
