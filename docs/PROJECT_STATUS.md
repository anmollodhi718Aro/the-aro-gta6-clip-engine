# Project Status

Last reviewed: 2026-11-18

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
- [x] Local-only FFmpeg renderer with rights confirmation, bounded duration, atomic no-overwrite publication, concurrent-output collision protection, and process timeout
- [x] Unit tests for detector, permission gates, CLI, YouTube adapter, clipper guards, and persistent consent registry
- [x] GitHub Actions compile and unit-test workflow

## Not implemented yet

- [x] SQLite-backed persistent creator/source consent registry with grant, expiry, scope checks, idempotent revocation, and audit events
- [ ] Consent registry authenticated management UI
- [x] Bounded YouTube REST polling worker with server-interval respect, stop event, batch/runtime limits, and permission re-check before every fetch
- [x] SQLite polling checkpoints with restart resume and callback-before-cursor-advance semantics
- [x] SQLite chat-event store with durable deduplication and conflicting event-ID rejection
- [x] Optional bounded official YouTube streamList/gRPC worker with checkpoint resume, consent re-checks, bounded reconnects, and durable persist-before-checkpoint ingestion
- [x] SQLite quota-aware multi-source scheduler with priority, per-source intervals, and atomic daily quota reservations
- [x] One-page scheduler-to-ingestion orchestration with consent recheck and persist-before-checkpoint ordering
- [ ] Continuous scheduler service, live quota calibration, and monitoring
- [ ] Video/chat clock synchronization
- [ ] Automatic selection of a valid video cut window from synchronized timestamps
- [ ] AI-assisted context and highlight scoring
- [ ] Caption generation and quality checks
- [ ] Web dashboard, authentication, database, and cloud queue
- [ ] Cloud worker and storage
- [ ] Human approval dashboard
- [ ] Platform upload adapters and OAuth approval
- [ ] Android application
- [ ] Billing, subscriptions, privacy policy, terms, and public launch readiness

## Known limits

- The REST adapter is a bounded page fetch. The optional official streamList/gRPC worker is bounded and resumable, not an always-on hosted service. REST and stream delivery are at-least-once: a crash after persistence/callback completion but before checkpoint commit can replay a batch.
- It only handles publicly accessible live chat via an API key; private account data and OAuth flows are not implemented.
- A local clip render is not evidence that a creator has granted distribution rights.
- Chat spike detection finds activity changes, not guaranteed entertaining or viral moments.
- Chat timestamps cannot be mapped to video offsets without a measured synchronization offset.
- GitHub Actions is CI, not a persistent 24/7 livestream worker.
- A green test run only validates the tests that actually ran.
