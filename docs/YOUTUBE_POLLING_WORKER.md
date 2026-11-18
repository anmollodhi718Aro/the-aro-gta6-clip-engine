# Bounded YouTube Polling Worker

The local MVP now includes a bounded REST polling worker as an intermediate ingestion step. It is not the final low-latency transport; the official streamList/gRPC worker remains planned.

## Contract

- Each run has an explicit batch limit (1 to 10,000) and runtime limit (greater than zero and at most 24 hours).
- The SQLite consent registry is checked before every API fetch. Missing, expired, revoked, or wrong-scope permission fails closed.
- The worker respects the server pollingIntervalMillis, with a five-second fallback when omitted, and never waits less than one second.
- Each batch is sent to a caller-provided callback. The callback owns durable storage and idempotent ingestion.
- It stops on a stop request, offline chat, batch limit, or runtime deadline.
- API and permission errors propagate. There are no silent retries.
- It does not download video, map timestamps, render clips, or publish content.

## Integration

```python
import threading
from backend.app.consent_registry import ConsentRegistry
from backend.app.youtube_live_chat import YouTubeLiveChatClient
from backend.app.youtube_polling_worker import run_bounded_polling

stop = threading.Event()
registry = ConsentRegistry("data/consent.sqlite3")
client = YouTubeLiveChatClient()  # reads YOUTUBE_API_KEY from environment
result = run_bounded_polling(
    client=client, registry=registry,
    video_id="AUTHORIZED_PUBLIC_VIDEO_ID",
    on_batch=process_and_persist_batch,
    stop_event=stop, max_batches=100, max_runtime_seconds=1800,
)
print(result)
```

The callback process_and_persist_batch is application-provided. It should persist events with idempotency keys and must not publish. Keep API credentials server-side.

## Restart-safe cursor storage

Pass a `PollingCheckpointStore` to persist the last successfully handled live-chat/page cursor. The store is keyed by video ID and uses SQLite. The callback runs before the checkpoint is advanced, so callback failures leave the previous cursor intact.

```python
from backend.app.polling_checkpoint_store import PollingCheckpointStore

checkpoints = PollingCheckpointStore("data/polling.sqlite3")
result = run_bounded_polling(
    client=client, registry=registry, video_id="AUTHORIZED_PUBLIC_VIDEO_ID",
    on_batch=process_and_persist_batch, stop_event=stop,
    max_batches=100, max_runtime_seconds=1800,
    checkpoint_store=checkpoints,
)
```

This is **at-least-once**, not exactly-once, delivery. A crash after the callback commits its events but before the checkpoint commits can replay a batch. The callback must be idempotent. Checkpoints do not replace event-level deduplication.

## Production gap

Add a queue with backpressure, monitoring, authenticated stop controls, managed database storage, and authorized integration tests before continuous operation. The REST worker remains a bounded transitional transport; prefer the official streamList/gRPC transport for low-latency ingestion once implemented and validated.