# THE ARO GTA 6 Clip Engine

A creator-first workflow for finding and preparing short highlights from **authorized** GTA 6 livestreams and recordings.

> This repository is the separate GTA 6 project. It is not the ARO History Engine.

## Current status

**Stage:** Local MVP core  
**Implemented:** permission-gated chat-spike detection, synthetic JSON demo, review-only clip plans, and local-only FFmpeg MP4 rendering.  
**Not yet implemented:** YouTube live-source integration, OAuth, chat/video clock synchronization, AI context analysis, dashboard, cloud workers, or publishing.

## MVP workflow

1. Analyze permitted chat/event data.
2. Detect unusual chat activity and produce explainable candidate timestamps.
3. Review candidate moments manually.
4. Render a short MP4 from a local media file that the operator owns or is authorized to process.
5. Keep distribution manual and owner-approved.

## Quick start

Python 3.11+ is required. FFmpeg is required only for local video rendering.

```bash
python -m backend.app.cli examples/sample_events.json --output clip_plan.json
python -m unittest discover -s tests -v
```

See [MVP usage](docs/MVP_USAGE.md) for event analysis and authorized local rendering.

## Repository map

- `backend/app/models.py`: timezone-aware permission and event models.
- `backend/app/detection.py`: deterministic, permission-gated chat-spike detector.
- `backend/app/cli.py`: local JSON analysis command.
- `backend/app/clipping.py`: local-only FFmpeg clip renderer.
- `examples/`: synthetic test data only.
- `tests/`: unit and CLI integration tests.
- `docs/`: plans, architecture, rights, security, testing, and owner actions.

## Safety and rights

Only use footage and data that you own or have permission to process. The clipper requires an explicit rights-confirmation flag, but that is an engineering guardrail, not legal verification. Creator permission does not automatically clear music, game publisher rights, or third-party content. See [Copyright and Permissions](docs/COPYRIGHT_POLICY.md).

## Development principles

- GitHub is the source of truth.
- Build in small, reviewable commits.
- Keep secrets out of Git.
- Use synthetic data or authorized sample assets first.
- Do not scrape, rip, or bypass platform controls.
- Do not map chat timestamps to video offsets without a measured clock synchronization offset.
- Automatic recovery must be bounded; code changes and production deployment require owner review.
- Publishing requires explicit human approval.

## Status and handoff

See [Project Status](docs/PROJECT_STATUS.md) for implemented and outstanding work, and [Owner Actions](docs/OWNER_ACTIONS.md) for tasks that require account-owner authorization or external setup.
