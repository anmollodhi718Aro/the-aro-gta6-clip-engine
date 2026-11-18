# Project Status

Last reviewed: 2026-11-18

## Implemented in the repository

- [x] Python 3.11+ project skeleton
- [x] Timezone-aware permission and chat event models
- [x] Permission-gated deterministic chat-spike detection
- [x] Idempotent duplicate event handling
- [x] Local JSON CLI and synthetic sample data
- [x] Review-only clip decision list; publishing is disabled
- [x] Local-only FFmpeg MP4 renderer with rights confirmation, bounded duration, no-overwrite behavior, and subprocess timeout
- [x] Unit tests for detector, permission gates, CLI, and clipper guards
- [x] GitHub Actions compile and unit-test workflow

## Not implemented yet

- [ ] Persistent creator/source consent registry and revocation UI
- [ ] Official YouTube Live Chat adapter and OAuth authorization
- [ ] Live source polling, reconnect logic, and quota-aware scheduling
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

- A local clip render is not evidence that a creator has granted distribution rights.
- Chat spike detection finds activity changes, not guaranteed entertaining or viral moments.
- Chat timestamps cannot be mapped to video offsets without a measured synchronization offset.
- GitHub Actions is CI, not a persistent 24/7 livestream worker.
- A green test run only validates the tests that actually ran.
