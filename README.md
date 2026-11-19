# THE ARO GTA 6 Clip Engine

A creator-first workflow for preparing original GTA 6 commentary and review-ready clips from media the channel owns or is explicitly authorized to process.

> This repository is the separate GTA 6 project. It is not the ARO History Engine.

## Current status

**Stage:** Local MVP with permission-gated source analysis, candidate review, local rendering, and original commentary production-pack generation.

## Quick start

Python 3.11+ is required. FFmpeg is required only for local video rendering.

```bash
python -m backend.app.cli examples/sample_events.json --output clip_plan.json
python -m unittest discover -s tests -v
```

## Original THE ARO content workflow

Prepare a sourced commentary and editing package from your own research notes:

```bash
python -m backend.app.content_studio research.json --output output/gta6_short.md --json-output output/gta6_short.json
```

Each factual beat must include a source URL and original THE ARO commentary. The generated package contains a voiceover draft, research checklist, visual plan, declared visual assets, description, and pre-upload review gate. The tool does not fetch or download third-party footage, verify claims, upload, or publish. See [Original Commentary Content Studio](docs/CONTENT_STUDIO.md).

Run the rights-aware visual preflight against declared assets before editing/publishing:

```bash
python -m backend.app.content_preflight output/gta6_short.json --rights-db state/rights.sqlite3 --platform youtube --output output/preflight_report.json
```

Third-party assets require recorded permission for both `edit` and `publish` on the target platform. A passing report only means recorded metadata matched; human verification and final review are still required. See [Rights-Aware Content Preflight](docs/RIGHTS_AWARE_PREFLIGHT.md).

## Source rights registry

Use the SQLite-backed registry to record the exact source, permission evidence reference, allowed uses, platforms, attribution, disclosure, and validity dates. Unknown, expired, revoked, or out-of-scope use is blocked. See [Source Rights Registry](docs/SOURCE_RIGHTS_REGISTRY.md).

## Existing pipeline

1. Analyze permitted chat/event data using official interfaces.
2. Detect unusual chat activity and produce explainable candidate timestamps.
3. Map timestamps only with a measured media-origin UTC timestamp.
4. Review candidates and rights manually.
5. Render locally from a media file the operator owns or is authorized to process.
6. Review the output in the local dashboard.
7. Keep upload/publishing manual and owner-approved.

Useful commands:

```bash
python -m backend.app.clip_pack youtube_clip_plan.json --media-origin-utc "2026-11-19T12:00:00+00:00" --output-dir clip_pack
python -m backend.app.candidate_quality clip_pack/clip_candidates.csv --output clip_pack/quality_scored_candidates.csv
python -m backend.app.review_dashboard rendered_clips/RUN_ID/batch_render_report.json --output rendered_clips/review.html
```

Batch rendering is dry-run by default and requires explicit row approvals plus rights confirmation to execute. It never uploads or publishes.

## Safety and rights

Credit and disclaimers do not replace permission. Creator permission may not cover music, game publisher rights, guests, or other third-party material. A registry entry is an engineering record, not legal verification. Do not scrape, rip, or bypass platform controls. When rights are uncertain, do not process or publish. See [Copyright and Permissions](docs/COPYRIGHT_POLICY.md).

## Development principles

- GitHub is the source of truth; work in feature branches and Draft PRs.
- Keep API keys and tokens out of Git.
- Use synthetic data or authorized sample assets first.
- Do not map chat timestamps to video offsets without measured synchronization.
- Respect API quota and platform rules.
- No automatic publishing. A human must approve each finished video.
- No paid dependencies.

See [Project Status](docs/PROJECT_STATUS.md) and [Owner Actions](docs/OWNER_ACTIONS.md) for implementation status and external setup.
