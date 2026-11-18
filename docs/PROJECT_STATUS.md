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
- [x] One-shot YouTube chat analysis CLI with pagination metadata
- [x] Review-only clip decision list; publishing is disabled
- [x] Local-only FFmpeg renderer with rights confirmation, bounded duration, no-overwrite behavior, and process timeout
- [x] Unit tests for detector, permission gates, CLI, YouTube adapter, clipper guards, and persistent consent registry
- [x] GitHub Actions compile and unit-test workflow

## Not implemented yet

- [x] SQLite-backed persistent creator/source consent registry with grant, expiry, scope checks, idempotent revocation, and audit events
- [ ] Consent registry authenticated management UI
- [ ] Continuous low-latency YouTube streamList/gRPC worker and reconnect logic
- [ ] Quota-aware scheduler across multiple live sources
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

- Current YouTube adapter is a bounded REST page fetch, not a continuous stream worker.
- It only handles publicly accessible live chat via an API key; private account data and OAuth flows are not implemented.
- A local clip render is not evidence that a creator has granted distribution rights.
- Chat spike detection finds activity changes, not guaranteed entertaining or viral moments.
- Chat timestamps cannot be mapped to video offsets without a measured synchronization offset.
- GitHub Actions is CI, not a persistent 24/7 livestream worker.
- A green test run only validates the tests that actually ran.
