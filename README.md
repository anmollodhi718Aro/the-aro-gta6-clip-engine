# THE ARO GTA 6 Clip Engine

A creator-first workflow for finding and preparing short highlights from **authorized** GTA 6 livestreams and recordings.

> This repository is the separate GTA 6 project. It is not the ARO History Engine.

## Current status

**Stage:** Local MVP core with measured chat-to-recording synchronization and a review-only clip-pack export.  
**Implemented:** permission-gated chat-spike detection, YouTube Live Chat API adapters, review-only clip plans, measured clock calibration, calibrated clip-pack CSV/Markdown exports, and local-only FFmpeg MP4 rendering.  
**Not yet implemented:** production-grade continuous live monitoring, OAuth/private-channel access, AI context analysis, complete dashboard, cloud workers, and owner-approved publishing.

## MVP workflow

1. Analyze permitted chat/event data.
2. Optionally fetch one bounded page of public live-chat events through the official YouTube Data API.
3. Detect unusual chat activity and produce explainable candidate timestamps.
4. Review candidate moments manually.
5. Render a short MP4 from a local media file that the operator owns or is authorized to process.
6. Keep distribution manual and owner-approved.

## Quick start

Python 3.11+ is required. FFmpeg is required only for local video rendering.

```bash
python -m backend.app.cli examples/sample_events.json --output clip_plan.json
python -m unittest discover -s tests -v
```

See [MVP usage](docs/MVP_USAGE.md), [calibrated clip-pack workflow](docs/CALIBRATED_CLIP_PACK.md), [clock synchronization](docs/CLOCK_SYNC.md), [YouTube adapter setup](docs/YOUTUBE_LIVE_CHAT.md), and [bounded polling worker](docs/YOUTUBE_POLLING_WORKER.md).

## Repository map

- `backend/app/models.py`: timezone-aware permission and event models.
- `backend/app/detection.py`: deterministic, permission-gated chat-spike detector.
- `backend/app/cli.py`: local JSON analysis command.
- `backend/app/clipping.py`: local-only FFmpeg clip renderer.
- `backend/app/clock_sync.py`: measured chat-to-recording clock calibration with residual/drift checks and no extrapolation.
- `backend/app/clip_pack.py`: calibrated chat-to-media offsets and collision-safe CSV/Markdown review exports.
- `backend/app/youtube_live_chat.py`: read-only YouTube public live-chat API adapter.
- `backend/app/youtube_cli.py`: one-page YouTube chat analysis command.
- `backend/app/consent_registry.py`: SQLite-backed creator consent and revocation audit registry.
- `backend/app/youtube_polling_worker.py`: bounded REST polling worker with consent re-checks and restart resume.
- `backend/app/youtube_stream_list_worker.py`: bounded official streamList/gRPC worker with checkpoint resume, consent re-checks, and transient reconnect handling.
- `backend/app/youtube_stream_list_grpc.py`: optional official gRPC transport adapter and protobuf-to-event conversion.
- `backend/app/youtube_stream_ingestion.py`: durable stream response handler that commits converted events before checkpoint advancement.
- `backend/app/polling_checkpoint_store.py`: SQLite page-token checkpoints for resumable polling.
- `backend/app/chat_event_store.py`: durable SQLite event ingestion with duplicate detection and conflicting-ID rejection.
- `backend/app/quota_scheduler.py`: SQLite multi-source due-time scheduler with atomic daily quota reservations.
- `backend/app/scheduled_ingestion.py`: one-page orchestration joining quota reservation, consent recheck, event persistence, and cursor checkpointing.
- `examples/`: synthetic test data only.
- `tests/`: unit and CLI integration tests.
- `docs/`: plans, architecture, rights, security, testing, and owner actions.

## Safety and rights

Only use footage and data that you own or have permission to process. The clipper requires an explicit rights-confirmation flag, but that is an engineering guardrail, not legal verification. Creator permission does not automatically clear music, game publisher rights, or third-party content. See [Copyright and Permissions](docs/COPYRIGHT_POLICY.md).

## Development principles

- GitHub is the source of truth.
- Build in small, reviewable commits.
- Keep API keys and tokens out of Git.
- Use synthetic data or authorized sample assets first.
- Do not scrape, rip, or bypass platform controls.
- Do not map chat timestamps to video offsets without a measured clock synchronization offset.
- Respect API quota and server-provided polling intervals.
- Automatic recovery must be bounded; code changes and production deployment require owner review.
- Publishing requires explicit human approval.

## Status and handoff

See [Project Status](docs/PROJECT_STATUS.md) for implemented and outstanding work, and [Owner Actions](docs/OWNER_ACTIONS.md) for tasks that require account-owner authorization or external setup.
