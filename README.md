# THE ARO GTA 6 Clip Engine

A creator-first workflow for finding and preparing short highlights from **authorized** GTA 6 livestreams and recordings.

> This repository is the separate GTA 6 project. It is not the ARO History Engine.

## Current status

**Implemented MVP foundation:** synthetic chat-event analysis, explainable candidate clip plans, and a local FFmpeg renderer for review-only clips from media the operator owns or is explicitly authorized to edit.

**Not yet implemented:** live stream monitoring, automatic platform ingestion, AI highlight detection, dashboard, mobile app, and public publishing.

The MVP is intentionally review-first. Candidate moments and rendered clips require human inspection before any separate distribution decision.

## MVP capabilities

1. Validate source permission metadata and supported event records.
2. Normalize event timestamps and identify unusual chat activity against a rolling baseline.
3. Produce deterministic candidate timestamps, scores, evidence, and `needs_review` status.
4. Render a local MP4 from an authorized local video file using FFmpeg.
5. Require explicit rights confirmation, constrain clip duration to 1–180 seconds, refuse output overwrites, and clean up failed temporary renders.
6. Run unit tests and a synthetic-video FFmpeg/FFprobe integration test in CI.

## Render an authorized local clip

Install FFmpeg and ensure it is available on PATH. From the repository root:

```bash
python -m backend.app.render_cli input_video.mp4 review_clip.mp4 --start 12.5 --duration 35 --confirm-rights
```

The output is a local review file only. This command does not download, upload, or publish media. Use only footage you own or are explicitly authorized to edit.

## Analyze synthetic chat events

With Python 3.11 or newer:

```bash
python -m backend.app.cli examples/sample_events.json --output clip_plan.json
python -m unittest discover -s tests -v
```

The included event fixture is synthetic and produces candidates marked for human review.

## Non-goals and safety

- No scraping, stream ripping, or bypassing platform controls.
- No automatic public uploads or publishing.
- No promise of virality, monetization, or unlimited free AI/API usage.
- No always-on cloud service until cost, quotas, security, and reliability are understood.
- Creator permission does not automatically clear third-party music, game footage, guests, or other content rights.
- Public uploads remain disabled until authenticated channel-owner approval, exact clip/source binding, and current rights checks are implemented and independently verified.

See [Copyright and Permissions](docs/COPYRIGHT_POLICY.md), [Master Plan](docs/MASTER_PLAN.md), [MVP Usage](docs/MVP_USAGE.md), and [Testing Plan](docs/TESTING_PLAN.md).

## Repository map

- `docs/`: project plan, architecture, security, testing, rights, and deployment notes.
- `backend/app/`: event analysis, permission checks, and local rendering CLI.
- `tests/`: unit and synthetic-media integration tests.
- `examples/`: synthetic event fixtures.

## Development principles

- GitHub is the source of truth.
- Build in small, reviewable commits.
- Keep secrets out of Git; use environment variables and a secrets manager.
- Test with synthetic data or authorized sample assets first.
- Publishing requires explicit human approval and must fail closed when identity or rights cannot be verified.
