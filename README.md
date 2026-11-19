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

\n## Make your first clip today\n\nIf you already have a local gameplay recording and know the moment timestamps, you can export a clip without waiting for chat analysis:\n\n```bash\npython -m backend.app.quick_clip "recordings/gta_gameplay.mp4" --start 42.5 --end 68 --output "clips/gta_moment_001.mp4" --confirm-rights\n```\n\nInstall FFmpeg first. Replace the example paths and times with your own. The command accepts local recordings, refuses to overwrite outputs, and requires confirmation that you own or are authorized to edit the recording. It creates a local MP4 only, not a vertical crop or upload. See [Quick Clip Guide](docs/QUICK_CLIP.md).\n\n## Original THE ARO content workflow

Prepare a sourced commentary and editing package from your own research notes:

```bash
python -m backend.app.content_studio research.json --output output/gta6_short.md --json-output output/gta6_short.json
```

Each factual beat must include a source URL and original THE ARO commentary. The generated package contains a voiceover draft, research checklist, visual plan, description, and pre-upload review gate. The tool does not fetch or download third-party footage, verify claims, upload, or publish. See [Original Commentary Content Studio](docs/CONTENT_STUDIO.md).

## Subtitle Studio

Format an operator-supplied timed transcript as SRT and run timing, overlap, line-length, and reading-speed checks:

```bash
python -m backend.app.subtitle_studio transcript.json --output output/captions.srt --report output/caption_quality.json
```

This does not transcribe audio or access video. Human review against the authorized source remains required. See [Subtitle Studio](docs/SUBTITLE_STUDIO.md).


## Review window selection

Select a bounded, non-overlapping shortlist from already detected and time-mapped candidates:

```python
from backend.app.window_selector import SelectionPolicy, select_review_windows

selected = select_review_windows(
    candidates, mapped_windows,
    SelectionPolicy(max_clips=5, min_gap_seconds=5, max_total_duration_seconds=300),
)
```

Selection is deterministic and review-only. It does not analyze gameplay frames/audio, approve rendering, or publish. See [Review Window Selector](docs/WINDOW_SELECTOR.md).

## Source rights registry

Use the SQLite-backed registry to record the exact source, permission evidence reference, allowed uses, platforms, attribution, disclosure, and validity dates. Unknown, expired, revoked, or out-of-scope use is blocked. See [Source Rights Registry](docs/SOURCE_RIGHTS_REGISTRY.md).

The local dashboard and the rights-aware preflight are designed to use the same `source_rights` SQLite registry. By default, the dashboard stores it at `aro_studio_data/source_rights.sqlite3`. PR #10 includes the shared registry adapter; the `content_preflight` CLI itself is introduced separately by Draft PR #9 and is not present in this PR #10 branch alone.

When the rights-aware preflight module from PR #9 is included in your checkout, point it at the dashboard database:

```bash
python -m backend.app.content_preflight output/gta6_short.json --rights-db aro_studio_data/source_rights.sqlite3 --platform youtube --output output/preflight_report.json
```

The dashboard is a local review surface, not an authorization service. Entered permission evidence still requires owner verification. Records from the earlier dashboard-only `rights` table are preserved and flagged for review; they are not silently treated as valid grants by the preflight.

## Local THE ARO Studio dashboard

Run the owner-local dashboard from the repository root:

```bash
python THE_ARO_STUDIO.py
```

Open `http://127.0.0.1:8765`. It reads local render reports, creates original commentary drafts, and writes permission records to the shared registry. Keep it on localhost. It does not download media, upload, publish, or approve content automatically.

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
