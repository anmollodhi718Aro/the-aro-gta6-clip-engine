# THE ARO GTA 6 Clip Engine

A creator-first workflow for finding and preparing short highlights from **authorized** GTA 6 livestreams and recordings.

> This repository is the separate GTA 6 project. It is not the ARO History Engine.

## Current status

**Stage:** Local MVP with permission-gated chat ingestion, measured clip planning, review-only rendering, and offline creator reporting tools.

Implemented across the open feature-branch work: deterministic chat-spike detection; official bounded YouTube chat adapters and resumable workers; SQLite consent, event, checkpoint and quota stores; measured chat-to-recording candidate export; human-approved local FFmpeg batch rendering and safe retry; offline clip-review dashboard; explainable candidate scoring; sourced original-commentary packs; source-rights metadata registry and visual-asset preflight; evidence-backed seven-day creator ranking; offline creator watchlist dashboard.

**Important:** These are feature-branch implementations and draft pull requests, not a claim that all changes are merged, CI-verified, deployed, or production-ready. See [Project Status](docs/PROJECT_STATUS.md).

## MVP workflow

1. Analyze permitted chat/event data.
2. Optionally fetch bounded public live-chat events through the official YouTube Data API.
3. Detect unusual chat activity and produce explainable candidate timestamps.
4. Map candidates to a local recording only with an operator-measured media-origin timestamp.
5. Review candidates manually.
6. Render only explicitly approved clips from local media the operator owns or is authorized to process.
7. Keep distribution manual and owner-approved.

## Quick start

Python 3.11+ is required. FFmpeg is required only for local video rendering.

```bash
python -m backend.app.cli examples/sample_events.json --output clip_plan.json
python -m unittest discover -s tests -v
```

### Creator watchlist report

Supply observed metrics with an exact seven-day UTC/offset-aware window and HTTPS evidence URL. Missing creators are omitted, never assigned invented metrics.

```bash
python -m backend.app.creator_watchlist_cli metrics.json --output creator_ranking.json
python -m backend.app.creator_watchlist_dashboard creator_ranking.json --output creator_watchlist.html
```

Open `creator_watchlist.html` locally. The page is self-contained and offline; it does not scrape metrics, download media, predict virality, or grant reuse rights. See [Creator Watchlist Dashboard](docs/CREATOR_WATCHLIST_DASHBOARD.md).

## Repository map

- `backend/app/models.py`: timezone-aware permission and event models.
- `backend/app/detection.py`: deterministic, permission-gated chat-spike detector.
- `backend/app/clipping.py`: local-only FFmpeg clip renderer.
- `backend/app/consent_registry.py`: SQLite-backed creator consent and revocation audit registry.
- `backend/app/youtube_polling_worker.py`: bounded REST polling worker with consent re-checks and restart resume.
- `backend/app/youtube_stream_list_worker.py`: bounded official streamList/gRPC worker.
- `backend/app/quota_scheduler.py` and `scheduled_ingestion.py`: SQLite quota-aware multi-source scheduling and ingestion orchestration.
- `backend/app/clip_pack.py`: measured chat-to-recording candidate export.
- `backend/app/batch_render.py`: dry-run-first, human-approved batch rendering and retry.
- `backend/app/candidate_quality.py`: explainable review scoring, not virality prediction.
- `backend/app/content_studio.py`: sourced original-commentary draft pack builder.
- `backend/app/rights_registry.py`: source-specific permission evidence metadata and fail-closed scope checks.
- `backend/app/creator_watchlist.py`: evidence-backed seven-day activity ranking.
- `backend/app/creator_watchlist_cli.py`: creator ranking JSON CLI with atomic output.
- `backend/app/creator_watchlist_dashboard.py`: offline HTML ranking dashboard.
- `examples/`: synthetic test data only.
- `tests/`: unit and CLI integration tests.
- `docs/`: architecture, rights, security, testing, and owner actions.

## Safety and rights

Only use footage and data that you own or have permission to process. The clipper's rights-confirmation flag is an engineering guardrail, not legal verification. Creator permission does not automatically clear music, game-publisher rights, or third-party content. See [Copyright and Permissions](docs/COPYRIGHT_POLICY.md).

- Do not scrape, rip, or bypass platform controls.
- Do not map chat timestamps to video offsets without a measured clock offset.
- Respect API quota and server-provided polling intervals.
- No automatic publishing; require manual owner approval.
- Do not promise virality or monetization.

## Development principles

- GitHub is the source of truth.
- Build in small, reviewable feature branches and draft PRs.
- Keep API keys and tokens out of Git.
- Use synthetic data or authorized sample assets first.
- A local render is not proof of distribution rights.
- CI is not a persistent 24/7 worker or production deployment.

## Status and handoff

See [Project Status](docs/PROJECT_STATUS.md) for implemented and outstanding work, and [Owner Actions](docs/OWNER_ACTIONS.md) for tasks requiring account-owner authorization or external setup.
