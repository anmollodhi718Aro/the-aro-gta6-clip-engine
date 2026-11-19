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
- [x] One-command offline pipeline from permission-gated chat events through measured clock mapping and quality-scored review pack
- [x] UTC chat candidate timestamps
- [x] Measured media-origin mapping to local file offsets
- [x] Multi-anchor clock calibration with residual/drift validation and no extrapolation
- [x] CSV and Markdown candidate packs with safe output handling
- [x] Explainable candidate review score with component reasons
- [x] Local FFmpeg rendering with duration/timeouts, explicit rights confirmation and no-overwrite publication
- [x] Local `ffprobe` inspection and pre-render rejection when selected clip bounds exceed actual media duration
- [x] Manual local clip-session CSV generator compatible with the reviewed batch renderer
- [x] One-command offline pipeline from permission-gated chat data through calibrated clip pack and quality-scored review CSV
- [x] Human-approved batch rendering and dry-run default
- [x] Collision-safe per-run directories and atomic JSON reports
- [x] Failed-only retry with candidate identity and time-bound verification
- [x] Offline HTML render review dashboard

### Original content and rights workflow
- [x] Original commentary content pack builder
- [x] Required research claims, source URLs and original commentary
- [x] Mandatory non-empty visual asset declarations with unique IDs and type/source-scope checks in content packs
- [x] SQLite source-rights registry with allowed uses/platforms, evidence reference, expiry and revocation
- [x] Rights-aware visual preflight for edit + publish scope on the exact platform
- [x] Required attribution/disclosure reporting
- [x] Human review remains mandatory and upload approval defaults to false

### Unified Studio and creator research
- [x] Local THE ARO Studio dashboard
- [x] Windows PowerShell launcher for the loopback-only Studio dashboard
- [x] Dashboard-generated content, preflight, clock-calibration and creator-watchlist files use collision-safe no-overwrite publication
- [x] Dashboard content/creator multi-file outputs roll back only files created by a failed publication attempt
- [x] Creator watchlist dashboard numeric validation imports and uses finite-number checks
- [x] Localhost-only request guard, CSRF validation and browser security headers
- [x] Dashboard writes to the shared source-rights registry
- [x] Dashboard content generator uses the shared content studio implementation
- [x] Dashboard visual preflight uses the shared rights registry
- [x] Dashboard measured-clock calibration with reusable anchor reports
- [x] Dashboard creator activity snapshot generation and offline HTML export
- [x] Seven-day evidence-backed creator activity ranking CLI
- [x] Atomic creator-ranking report output
- [x] Offline creator watchlist dashboard with escaped fields and HTTPS-only evidence links
- [x] Subtitle Studio for supplied timed transcripts and quality checks
- [x] Optional official YouTube OAuth upload CLI with dry-run default, local token storage, exact rights-report gate, owner approval, and explicit audience declaration

## Test inventory

The integrated branch contains 36 files under `tests/` (35 Python test modules plus `tests/README.md` and one test-support file), including coverage for:
- Core event models and detection
- Consent registry, chat event storage and quota scheduler
- YouTube adapter, workers, stream ingestion and multi-source lifecycle
- Clip analysis CLI, timestamp mapping, ffprobe media validation, FFmpeg rendering and batch rendering
- End-to-end synthetic chat-to-clip preparation smoke test
- Output safety, retry validation and local dashboards
- Candidate scoring
- Original content studio and rights preflight
- Source rights registry
- Manual clip session and end-to-end pipeline
- Creator watchlist and CLI
- Subtitle quality
- Synthetic end-to-end chat-to-candidate-to-scored-review-to-batch-dry-run workflow

A test file being present is not proof it passed. The candidate includes an end-to-end synthetic smoke test spanning chat analysis, measured clock mapping, clip-pack export, quality scoring and batch dry-run. Run the exact suite on the latest integrated commit and record the result. GitHub Actions issue #26 tracks jobs that fail before runner assignment (runner_id 0, no steps/logs); remote CI execution remains unverified, not that all tests passed.

## Not implemented / external setup still required

- [ ] Owner creates a Google Cloud Desktop OAuth client and enables YouTube Data API v3
- [ ] Test OAuth consent and first upload against a private/unlisted owner-created video
- [ ] Verify channel-side upload settings and audience declaration in a real account
- [ ] Packaged Windows desktop executable/installer
- [ ] Automatic speech-to-text; Subtitle Studio requires supplied timed transcripts
- [ ] Automatic visual highlight recognition from video frames/audio
- [ ] Automatic synchronization marker detection; current mapping requires manually measured origin or three+ manually matched anchors
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
- No automatic upload scheduling or unattended publishing is implemented; the optional YouTube uploader is a one-shot CLI requiring manual owner approval.

## Owner-side actions before first real clip

1. Use footage the owner created or is expressly authorized to edit and publish.
2. Ensure the exact source permission and platform scope is recorded.
3. Supply the authorized local media file.
4. Supply a measured UTC media-origin timestamp or at least three calibrated clock anchors for that exact recording.
5. Run the pipeline, inspect the candidate pack, approve specific rows and review rendered files.
6. Configure a Google Cloud Desktop OAuth client, then test the manual uploader with a private/unlisted owner-created video before any public upload.
