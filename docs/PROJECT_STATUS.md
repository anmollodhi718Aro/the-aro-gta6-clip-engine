# THE ARO GTA 6 Clip Engine — Project Status

Last reviewed: 2026-11-19

## Branch and release state

- Integrated candidate branch: `integration/release-candidate`
- Source baseline: single-file Studio feature line plus latest reviewed changes from the previously separate feature branches.
- This branch is a consolidated release candidate for review.
- The default `main` branch has not been modified.
- No pull request has been merged by this integration work.
- CI must be checked on the integrated PR head before a release decision.

## Implemented in the integrated candidate

### Core source and chat processing
- [x] Python 3.11+ package and standard-library-first design
- [x] Timezone-aware permission and chat event models
- [x] Permission-gated chat-spike detection
- [x] Idempotent event storage and duplicate/conflicting event handling
- [x] SQLite consent registry with grant, expiry, scope, revocation and audit
- [x] Bounded YouTube public live-chat REST adapter
- [x] Bounded polling worker with stop controls and per-fetch consent re-check
- [x] Durable polling checkpoints and event persistence
- [x] Quota-aware multi-source scheduler and bounded lifecycle service
- [x] Optional official YouTube streamList/gRPC adapter and worker

### Clip candidate and local rendering
- [x] Local JSON analysis CLI
- [x] UTC chat candidate timestamps
- [x] Measured media-origin mapping to local file offsets
- [x] CSV and Markdown candidate packs with safe output handling
- [x] Explainable candidate review score with component reasons
- [x] Local FFmpeg rendering with duration/timeouts, explicit rights confirmation and no-overwrite publication
- [x] Human-approved batch rendering and dry-run default
- [x] Collision-safe per-run directories and atomic JSON reports
- [x] Failed-only retry with candidate identity and time-bound verification
- [x] Offline HTML render review dashboard

### Original content and rights workflow
- [x] Original commentary content pack builder
- [x] Required research claims, source URLs and original commentary
- [x] Visual asset declarations in content packs
- [x] SQLite source-rights registry with allowed uses/platforms, evidence reference, expiry and revocation
- [x] Rights-aware visual preflight for edit + publish scope on the exact platform
- [x] Required attribution/disclosure reporting
- [x] Human review remains mandatory and upload approval defaults to false

### Unified Studio and creator research
- [x] Local THE ARO Studio dashboard
- [x] Localhost-only request guard, CSRF validation and browser security headers
- [x] Dashboard writes to the shared source-rights registry
- [x] Dashboard content generator uses the shared content studio implementation
- [x] Dashboard visual preflight uses the shared rights registry
- [x] Seven-day evidence-backed creator activity ranking CLI
- [x] Atomic creator-ranking report output
- [x] Subtitle Studio for supplied timed transcripts and quality checks

## Test inventory

The integrated branch contains 28 test/documentation files under `tests/`, including coverage for:
- Core event models and detection
- Consent registry, chat event storage and quota scheduler
- YouTube adapter, workers, stream ingestion and multi-source lifecycle
- Clip analysis CLI, timestamp mapping, FFmpeg rendering and batch rendering
- Output safety, retry validation and local dashboards
- Candidate scoring
- Original content studio and rights preflight
- Source rights registry
- Creator watchlist and CLI
- Subtitle quality

A test file being present is not proof it passed. Run the exact suite on the latest integrated commit and record the result. The GitHub Actions failures previously observed often ended before the job exposed any steps/logs; this means remote CI execution remains unverified, not that all tests passed.

## Not implemented / external setup still required

- [ ] Google OAuth desktop authorization for the owner's YouTube channel
- [ ] YouTube Data API upload adapter with explicit per-video approval
- [ ] Real uploader integration test on a private/unlisted test video
- [ ] Packaged Windows desktop executable/installer
- [ ] Automatic speech-to-text; Subtitle Studio requires supplied timed transcripts
- [ ] Automatic visual highlight recognition from video frames/audio
- [ ] Automatic chat-to-video synchronization; operator must measure media origin
- [ ] Official access to video-file bytes; YouTube chat APIs do not provide VOD files
- [ ] Persistent cloud workers, distributed queue, remote storage or 24/7 runtime
- [ ] Public multi-user authentication, privacy policy, terms and production security review
- [ ] Production backup/restore and recovery drills

## Important product limits

- Public livestream availability does not authorize downloading/reposting. Process media only when owned or explicitly authorized for the intended edit and distribution.
- Creator credit and disclaimers do not substitute for permission.
- Game publisher, music, guests and other embedded third-party rights may need separate clearance.
- Chat spikes are candidate signals, not guaranteed highlights or viral clips.
- Quality scores are heuristic sorting aids, not predictions of reach or monetization.
- Rights preflight validates stored metadata, not the authenticity or legal sufficiency of permission evidence.
- No automated upload or publishing is implemented; human review is required.

## Owner-side actions before first real clip

1. Use footage the owner created or is expressly authorized to edit and publish.
2. Ensure the exact source permission and platform scope is recorded.
3. Supply the authorized local media file.
4. Supply a measured UTC media-origin timestamp for that exact recording.
5. Run the pipeline, inspect the candidate pack, approve specific rows and review rendered files.
6. If publishing is later implemented, configure an OAuth app and test privately before any public upload.
