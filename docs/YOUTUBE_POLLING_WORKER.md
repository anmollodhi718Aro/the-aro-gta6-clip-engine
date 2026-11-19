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
from backend.app.chat_event_store import ChatEventStore

checkpoints = PollingCheckpointStore("data/polling.sqlite3")
events = ChatEventStore("data/events.sqlite3")
result = run_bounded_polling(
    client=client, registry=registry, video_id="AUTHORIZED_PUBLIC_VIDEO_ID",
    on_batch=events.persist_batch, stop_event=stop,
    max_batches=100, max_runtime_seconds=1800,
    checkpoint_store=checkpoints,
)
```

This is **at-least-once**, not exactly-once, delivery. A crash after the callback commits its events but before the checkpoint commits can replay a batch. `ChatEventStore.persist_batch` provides durable event-level deduplication: identical re-deliveries are counted as duplicates, while conflicting reuse of an event ID is rejected. Event persistence and cursor advancement are separate SQLite transactions, so a crash between them safely causes a harmless replay rather than a skipped batch.

## Production gap

Add a queue with backpressure, monitoring, authenticated stop controls, managed database storage, and authorized integration tests before continuous operation. The REST worker remains a bounded transitional transport; prefer the official streamList/gRPC transport for low-latency ingestion once implemented and validated.
## Multi-source quota scheduling

`QuotaAwareScheduler` is a separate allocation component. It stores source intervals, priorities, enabled state, and request-cost units in SQLite. `claim_next` atomically selects one due source and reserves its configured units against a daily UTC budget. Reservations are conservative and are not refunded after a failed request.

```python
from backend.app.quota_scheduler import QuotaAwareScheduler

scheduler = QuotaAwareScheduler("data/scheduler.sqlite3")
scheduler.configure_source(
    "AUTHORIZED_PUBLIC_VIDEO_ID",
    interval_seconds=10,
    request_cost_units=5,  # operator-configured estimate, not an API guarantee
    priority=10,
)
job = scheduler.claim_next(daily_quota_units=1000)
if job is not None:
    # Before network access, still check ConsentRegistry.require(...).
    # Then perform one bounded fetch and persist the returned batch.
    print(job.source_id, job.quota_remaining_today)
```

The scheduler does not itself call YouTube, validate creator consent, or calibrate API costs. The caller must check consent immediately before network access and configure request costs from current official quota documentation. It reserves budget before the call, so failures consume the reservation conservatively. This is a scheduling primitive, not a production multi-tenant service.
## One-page scheduler orchestration

`poll_one_due_source` connects the scheduler to the existing consent registry, read-only YouTube client, event store, and checkpoint store. Each call claims at most one due source, rechecks `analyze_chat` consent immediately before the API request, fetches one page, persists events, and only then advances the cursor. If consent is revoked, the API call is blocked. The quota reservation remains consumed conservatively even if consent validation or the request fails.

```python
from backend.app.scheduled_ingestion import poll_one_due_source

result = poll_one_due_source(
    scheduler=scheduler, registry=registry, client=client,
    checkpoints=checkpoints, events=events, daily_quota_units=1000,
)
if result is not None:
    print(result.reservation.source_id, result.ingestion)
```

This is a one-shot orchestration primitive, not a continuously running service. A production loop still needs operator-controlled lifecycle, monitoring, backpressure, and quota configuration from current provider documentation.