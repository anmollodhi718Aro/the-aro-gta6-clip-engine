# Project Status

Last reviewed: 2026-11-19

## Implemented in the repository

- [x] Python 3.11+ project skeleton
- [x] Timezone-aware permission and chat event models
- [x] Permission-gated deterministic chat-spike detection
- [x] Idempotent duplicate event handling
- [x] Local JSON CLI and synthetic sample data
- [x] Read-only one-page YouTube public live-chat REST adapter
- [x] Permission check before YouTube chat API access
- [x] YouTube one-shot CLI integration with SQLite consent registry (JSON permission file remains supported)
- [x] One-shot YouTube chat analysis CLI with pagination metadata
- [x] Review-only clip decision list; publishing is disabled
- [x] Local-only FFmpeg renderer with rights confirmation, bounded duration, no-overwrite behavior, and process timeout\n- [x] One-command manual quick-clip CLI for a local gameplay recording
- [x] Unit tests for detector, permission gates, CLI, YouTube adapter, clipper guards, and persistent consent registry
- [x] GitHub Actions compile and unit-test workflow

## Not implemented yet

- [x] SQLite-backed persistent creator/source consent registry with grant, expiry, scope checks, idempotent revocation, and audit events
- [ ] Consent registry authenticated management UI
- [x] Bounded YouTube REST polling worker with server-interval respect, stop event, batch/runtime limits, and permission re-check before every fetch
- [x] SQLite polling checkpoints with restart resume and callback-before-cursor-advance semantics
- [x] SQLite chat-event store with durable deduplication and conflicting event-ID rejection
- [ ] Continuous low-latency YouTube streamList/gRPC worker and reconnect/resume logic
- [x] SQLite quota-aware multi-source scheduler with priority, per-source intervals, and atomic daily quota reservations
- [x] One-page scheduler-to-ingestion orchestration with consent recheck and persist-before-checkpoint ordering
- [ ] Continuous scheduler service, live quota calibration, and monitoring
- [x] Operator-measured video/chat timestamp mapping with bounds validation (manual offset required)
- [ ] Automatic video/chat clock synchronization and offset calibration
- [x] Deterministic review-only selection of mapped, non-overlapping clip windows with count/duration limits
- [ ] Automatic scene-aware cut-window detection from video frames/audio
- [ ] AI-assisted context and highlight scoring
- [x] Deterministic SRT formatting and caption quality checks from operator-supplied timed transcripts
- [ ] Web dashboard, authentication, database, and cloud queue
- [ ] Cloud worker and storage
- [ ] Human approval dashboard
- [ ] Platform upload adapters and OAuth approval
- [ ] Android application
- [ ] Billing, subscriptions, privacy policy, terms, and public launch readiness

- Subtitle Studio formats supplied timed text; it does not transcribe audio, synchronize captions automatically, or verify caption accuracy. Human review remains required.

## Known limits

- Current YouTube adapter is a bounded REST page fetch, not a continuous stream worker. REST polling checkpoints support restart resume, but delivery is at-least-once: a crash after callback completion and before checkpoint commit can replay a batch.
- It only handles publicly accessible live chat via an API key; private account data and OAuth flows are not implemented.
- A local clip render is not evidence that a creator has granted distribution rights.
- Chat spike detection finds activity changes, not guaranteed entertaining or viral moments.
- Chat timestamps can be mapped to video offsets only when an operator supplies a measured offset; automatic synchronization and calibration are not implemented.
- The window selector ranks existing chat candidates only. It does not inspect gameplay frames/audio or identify scene boundaries.
- Latest observed GitHub Actions jobs terminate before reporting any steps; job logs are unavailable from GitHub, so the test suite result is currently unverified.\n- GitHub Actions is CI, not a persistent 24/7 livestream worker.
- A green test run only validates the tests that actually ran.
