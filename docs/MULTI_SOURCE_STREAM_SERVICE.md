# Multi-source stream service

`backend.app.youtube_multi_source_service.MultiSourceStreamService` is an
optional lifecycle manager around the bounded streamList worker. It is inert
until the application explicitly calls `start_source`.

## Safety and lifecycle

- Configure a fixed concurrency ceiling from 1 to 32 sources.
- Start each source explicitly with its video ID, live-chat ID, transport
  factory, and durable response callback.
- The wrapped worker re-checks the SQLite consent registry before every
  connection and reconnect. The required scope is `analyze_chat`.
- A source has an independent stop event. `stop_source` requests that stop and
  joins for at most the supplied timeout.
- `shutdown` requests all active sources to stop and uses one shared join
  deadline. It returns IDs that are still active after that deadline.
- `status` exposes running, finished, or failed state and the bounded worker
  result/error for health reporting.
- A completed source can be explicitly started again. A source already running
  cannot be started twice.
- The service does not discover streams, create credentials, auto-start,
  publish content, or download video.

## Example

```python
from backend.app.consent_registry import ConsentRegistry
from backend.app.youtube_multi_source_service import MultiSourceStreamService

registry = ConsentRegistry("data/consent.sqlite3")
service = MultiSourceStreamService(
    registry=registry,
    max_concurrent_sources=2,
)

# Supply an official generated-gRPC stream factory and a callback that commits
# each response to ChatEventStore before returning.
service.start_source(
    video_id="authorized-video-id",
    live_chat_id="active-live-chat-id",
    stream_factory=stream_factory,
    on_response=durable_response_handler,
    max_responses=500,
    max_runtime_seconds=1800,
    max_reconnects=3,
)

print(service.status())
# Stop one source:
service.stop_source("authorized-video-id")
# Or stop all sources:
still_running = service.shutdown(join_timeout=5)
```

## Delivery semantics

The underlying stream worker commits the response callback before advancing
its SQLite page-token checkpoint. Delivery remains at-least-once: a crash
between durable event commit and checkpoint commit can replay a response.
Callbacks should therefore use the existing idempotent event store. A blocked
transport iterator may not react immediately to a stop event; shutdown reports
workers that remain active after the join deadline rather than claiming they
have stopped.

This service is a process-local lifecycle primitive, not a distributed worker
or production hosting system. Do not run multiple service instances against the
same source IDs without an external lease/ownership mechanism.
