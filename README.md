# THE ARO GTA 6 Clip Engine

A local-first, zero-mandatory-dependency creator workflow for analysing authorized GTA 6 livestream chat, reviewing clip candidates, rendering from locally supplied authorized media, and producing original THE ARO commentary packs.

> This is the separate GTA 6 project, not the ARO History Engine or THE ARO Deployment Network.

## Start clipping today

**Fastest Windows route:** install Python 3.11+ and FFmpeg (including ffprobe), then double-click `START_CLIPPING_TODAY.bat`. It guides you through selecting up to 50 moments from a local recording, optionally renders full-frame 1080×1920 (9:16) Shorts output, runs a dry-run, requires two explicit confirmations before rendering, and opens a local review dashboard. See [Manual Clipping](docs/MANUAL_CLIPPING.md). Before the first real session, run the project checks with `powershell -ExecutionPolicy Bypass -File scripts/check_project.ps1`. The latest recorded hosted CI evidence in the current draft stack is run [#45400525644](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45400525644): Ubuntu and hosted Windows each passed compilation, the same 346-test suite, and synthetic MP4/FFprobe validation on PR #302's merge ref. This is merge-ref CI evidence only; it is not raw-head-only proof, owner-device Windows verification, or authorized real-media acceptance. See `docs/PROJECT_HANDOFF.md` for project handoff evidence and current blockers.

For the full chat-assisted workflow and measured timestamp synchronization, see [First Clip Today](docs/FIRST_CLIP_TODAY.md).

## Requirements

- Python 3.11+
- FFmpeg and ffprobe on PATH for actual local video rendering and media preflight.
- No mandatory third-party Python packages.
- Optional YouTube stream/gRPC adapter dependencies: `pip install -e ".[youtube-stream]"`.
- A YouTube Data API key is required only for supported public live-chat API operations. Keep credentials in local environment configuration; never commit them.

## Start the unified local dashboard

```bash
python THE_ARO_STUDIO.py
```

Open `http://127.0.0.1:8765`. The dashboard is intentionally loopback-only and includes:

**Windows PowerShell one-command launcher:**

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_studio.ps1
```

Keep the PowerShell window open while using the dashboard. See [First Clip Today](docs/FIRST_CLIP_TODAY.md) for the Windows walkthrough.

- Local batch-render report overview.
- Original commentary content-pack generator.
- Shared SQLite source-rights metadata form.
- Rights-aware visual preflight form.
- CSRF and local-origin request protections.

Data defaults:
- `rendered_clips/`: local render reports and outputs.
- `aro_studio_data/source_rights.sqlite3`: shared permission metadata.
- `aro_studio_data/content_packs/`: generated content drafts.
- `aro_studio_data/preflight_reports/`: preflight reports.

## End-to-end local workflow

### 1. Detect chat spikes

Use authorized chat event data. The analyzer detects unusual chat activity, not guaranteed entertaining moments.

```bash
python -m backend.app.cli examples/sample_events.json --output clip_plan.json
```

### 2. Map chat candidates to the exact local recording

The media origin must be measured for the exact recording. A single measured offset is supported:

```bash
python -m backend.app.clip_pack clip_plan.json \
  --media-origin-utc "2026-11-19T12:00:00+00:00" \
  --output-dir clip_pack
```

For drift-aware calibration, supply at least three independently measured anchors from the same authorized source:

```bash
python -m backend.app.clip_pack clip_plan.json \
  --clock-anchors-json examples/clock_anchors.example.json \
  --output-dir clip_pack
```

The multi-anchor fit rejects excessive residual/drift and refuses timestamps outside the calibrated interval. The example anchor file is synthetic; replace it with real measurements from the exact recording. The command produces CSV and Markdown review sheets. It never downloads or extracts livestream video.

### 3. Score candidate review suitability

```bash
python -m backend.app.candidate_quality clip_pack/clip_candidates.csv \
  --output clip_pack/quality_scored_candidates.csv
```

The 0-100 heuristic explains chat-activity, duration, and synchronization points. It does not predict views or virality and does not approve a clip.

### 4. Preview a batch render

```bash
python -m backend.app.batch_render clip_pack/clip_candidates.csv \
  --media "/path/to/authorized-local-recording.mp4" \
  --approve 1,3 \
  --output-dir rendered_clips
```

Dry-run is the default. Every execution uses a unique run directory and an atomic JSON report.

### 5. Render only after explicit review

```bash
python -m backend.app.batch_render clip_pack/clip_candidates.csv \
  --media "/path/to/authorized-local-recording.mp4" \
  --approve 1,3 \
  --output-dir rendered_clips \
  --execute --confirm-rights
```

The operator must own or be authorized to process the exact local media. Only explicitly selected rows are considered. Non-renderable rows are blocked. Before actual rendering, `ffprobe` verifies a video stream and checks the real file duration; audio-only files and candidates extending beyond the file are rejected.

To retry only failed rows, use the prior run's report:

```bash
python -m backend.app.batch_render clip_pack/clip_candidates.csv \
  --media "/path/to/authorized-local-recording.mp4" \
  --retry-report rendered_clips/RUN_ID/batch_render_report.json \
  --output-dir rendered_clips
```

Retry defaults to dry-run and verifies source ID, time bounds, and exact local media identity (resolved path, size, and modification timestamp). Old reports without media identity are not retryable through the CLI.

### 6. Review output locally

```bash
python -m backend.app.review_dashboard \
  rendered_clips/RUN_ID/batch_render_report.json \
  --output rendered_clips/review.html
```

Open the HTML file locally. It is read-only and has no remote assets or network requests.

## Original THE ARO content studio

Prepare a sourced, original commentary package from operator-supplied research:

```bash
python -m backend.app.content_studio research.json \
  --output output/gta6_short.md \
  --json-output output/gta6_short.json
```

Each factual beat requires a source URL and original THE ARO commentary. A generated package includes a voiceover draft, source checks, visual plan, metadata, and a closed human-review gate.

## Source rights and visual preflight

The SQLite registry records source ID, grantor, evidence reference, allowed uses, platforms, attribution/disclosure, validity, expiry and revocation.

Run the fail-closed preflight:

```bash
python -m backend.app.content_preflight output/gta6_short.json \
  --rights-db aro_studio_data/source_rights.sqlite3 \
  --platform youtube \
  --output output/preflight_report.json
```

For each declared third-party visual, the preflight requires both `edit` and `publish` scope on the target platform. A matching record is metadata only, not legal verification. All included music, game publisher, guest and other third-party rights need separate review. Credit and a disclaimer do not replace permission.

### Optional YouTube uploader: private-only owner approval

The uploader is opt-in and its live upload boundary currently permits **PRIVATE staging only**. The current draft implementation is not integrated into the default branch, and no real upload has been accepted. Keep OAuth client files, tokens, destination profiles, and approval records local and out of Git.

For multiple destinations, store a non-secret profile map at `.secrets/youtube_destination_profiles.json`. Each profile maps a verified Google OIDC `sub` to the exact YouTube channel ID. The profile loader requires this file to resolve directly inside this repository's `.secrets/` directory; profile-specific OAuth tokens are isolated under `.secrets/tokens/<profile>.json`. Never infer a channel ID from a public handle. Each destination must be verified through its own authorized OAuth session and `channels.list(mine=True)` result. The CLI does not allow a shared `--token` override when a destination profile is selected. A legacy single-destination configuration may use `ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT` and `ARO_YOUTUBE_CHANNEL_ID` locally.

First, record approval for one exact local video, clip ID, source ID, destination and PRIVATE visibility. This separate command does not upload:

```bash
python -m backend.app.youtube_upload /path/to/authorized-clip.mp4 \\
  --rights-report output/preflight_report.json \\
  --title "THE ARO clip" --not-made-for-kids --privacy private \\
  --destination-config .secrets/youtube_destination_profiles.json \\
  --destination-profile PROFILE_NAME \\
  --approve-clip --clip-id CLIP_ID --source-id SOURCE_ID \\
  --approval-record .secrets/approvals/PROFILE_NAME/CLIP_ID.json \\
  --rights-db aro_studio_data/source_rights.sqlite3
```

The owner must authenticate through the loopback OAuth flow. The signed Google ID token is checked against the OAuth client ID, issuer and configured subject; the same OAuth session must resolve to the configured channel through `channels.list(mine=True)`. The command rechecks current YouTube publish permission and asks for `APPROVE PRIVATE <clip_id>`. The non-overwritable approval expires after 24 hours by default and binds the Google subject, channel, clip/source IDs, PRIVATE visibility and exact local video SHA-256.

A separate, deliberate upload invocation requires the same destination profile, exact clip/source IDs, approval record, `--privacy private`, `--upload --owner-approved --confirm-rights`, and fresh identity, approval and rights checks immediately before `videos.insert`. The API response must contain a video ID and explicitly confirm `status.privacyStatus == "private"`; otherwise the result is UNVERIFIED and must be inspected in YouTube Studio. The two boolean flags are additional acknowledgements, never identity authentication.

**Unlisted and public live uploads are rejected by the current uploader.** Do not use an unlisted/public approval phrase or treat a dry-run metadata validation as upload permission. Unit tests use mocked OAuth/YouTube clients and never perform a network upload. See [YouTube Upload Adapter](docs/YOUTUBE_UPLOAD.md) for the current detailed procedure and limits.

## Seven-day creator activity watchlist

Supply evidence-backed metrics; the tool does not scrape creators or download media.

```bash
python -m backend.app.creator_watchlist_cli \
  examples/creator_metrics.example.json \
  --output output/creator_ranking.json
```

Metrics must cover exactly seven timezone-aware days and include an HTTPS evidence URL. Missing creators remain unranked rather than receiving invented zero values. Results describe historical activity, not future virality or permission to reuse content.

Build the offline HTML view:

```bash
python -m backend.app.creator_watchlist_dashboard output/creator_ranking.json --output output/creator_watchlist.html
```

Open the generated file locally. It escapes untrusted report fields, only links HTTPS evidence URLs, and contains no remote assets or tracking.

## Subtitle Studio

Format an operator-supplied timed transcript and run caption-quality checks:

```bash
python -m backend.app.subtitle_studio transcript.json \
  --output output/captions.srt \
  --report output/caption_quality.json
```

This does not transcribe audio or synchronize captions automatically. Human review is required.

## Manual clip session (no chat export required)

When you already have a local recording but no synchronized chat data, select time ranges in your editor and create a batch-render CSV:

```bash
python -m backend.app.manual_clip examples/manual_clips.example.json --output manual_clips.csv
python -m backend.app.batch_render manual_clips.csv \
  --media "/path/to/your-authorized-recording.mp4" \
  --approve 1 \
  --output-dir rendered_clips
```

This first command creates review rows only. The batch renderer is dry-run by default. Only after reviewing the selected range and confirming rights should you rerun with `--execute --confirm-rights`. See [Manual Clipping](docs/MANUAL_CLIPPING.md).

## Test suite

Run all local checks:

**Windows PowerShell**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_project.ps1
```

**Linux / macOS / Git Bash**
```bash
bash scripts/check_project.sh
```

Equivalent direct commands:
```bash
python -m compileall -q backend tests THE_ARO_STUDIO.py
python -m unittest discover -s tests -v
```

GitHub Actions runs the same compile and unittest discovery workflow on pull requests. A CI job that fails before steps execute is not evidence of code-test failure, but it is also not a passing test result. See [Local Validation](docs/LOCAL_CHECKS.md).

## Explicit limitations / not yet production-ready

- No official YouTube video-file download or livestream ripping is implemented.
- YouTube chat access does not provide the stream's video bytes. Video must be separately supplied as a local file with adequate rights.
- No fully automatic chat-to-video synchronization: mapping requires a manually measured single origin or at least three calibration anchors; the clock fit refuses extrapolation.
- No packaged Windows desktop installer; the current unified app is a local Python HTTP dashboard.
- The authenticated per-clip uploader and private-only response checks are implemented in the open draft PR stack rooted at PR #299, with regression/CI follow-ups in PRs #301–#303; this work is not merged into the default branch. Owner-side OAuth setup, independent security review, owner-controlled integration, owner-device verification, and an authorized PRIVATE real-media acceptance test remain outstanding. No real upload has been performed or accepted.
- No automatic posting, background cloud worker, billing, or monetization guarantee.
- The creator watchlist only ranks supplied, evidence-backed metrics.
- A score or successful rights-metadata preflight is not an upload or monetization approval.

## Development rules

- GitHub remains the source of truth.
- Work on feature/integration branches and review through PRs.
- Keep API keys, OAuth client secrets and tokens out of Git.
- No scraping, stream ripping, fake engagement, quota evasion, or platform-control bypass.
- No automatic publication. Human approval is required for every final upload.
- No paid dependencies are required by the core local workflow; the optional official uploader uses free/open-source Python client libraries and Google's API quota.

See `docs/PROJECT_STATUS.md`, `docs/TESTING_PLAN.md`, and the feature-specific docs for implementation details.
## One-command offline review pipeline

Build a local scored review pack from permission-gated chat-event JSON and at least three measured clock anchors:

```bash
python -m backend.app.pipeline events.json --clock-anchors-json clock_anchors.json --output-dir aro_pipeline_run
```

The command writes a clip plan, measured candidate CSV/Markdown, explainable quality scores and a pipeline summary. The output directory must be new; existing owner files are never overwritten. It does not download, render, upload or publish video. Human review and separate authorization checks remain required before local rendering.
