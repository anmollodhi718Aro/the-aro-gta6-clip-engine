# THE ARO GTA 6 Clip Engine

A creator-first workflow for finding and preparing short highlights from **authorized GTA 6 recordings and streams**.

> This repository is the separate GTA 6 project. It is not the ARO History Engine.

## Current status

**Local MVP:** chat-spike candidate detection plus permission-gated FFmpeg clipping from a local video file.  
**Not yet implemented:** live monitoring, video/audio AI highlight detection, dashboard, platform integrations, or publishing.

## Implemented

1. Permission-gated analysis of chat event JSON.
2. Deterministic chat-spike detection and reviewable clip decision lists.
3. Permission-gated local MP4 clipping with FFmpeg.
4. Optional 9:16, 1080x1920 center-cropped output.
5. Unit tests and GitHub Actions CI.

## Start clipping

Requirements: Python 3.11+, FFmpeg, and FFprobe.

Create a permission file for footage you own or are authorized to use:

```json
{
  "source_id": "my-recording",
  "granted_by": "owner-or-license-attestation",
  "scopes": ["render_video"],
  "granted_at": "2026-11-19T00:00:00+05:30"
}
```

Render a vertical 35-second clip starting at 45 seconds:

```bash
python -m backend.app.clip_cli recording.mp4 output/clip-001.mp4 --start 45 --duration 35 --permission permission.json --confirm-authorized --vertical
```

Remove `--vertical` to preserve the source aspect ratio. The command works only with a local file, validates the requested range, requires an explicit authorization attestation, and never publishes automatically.

For chat-based candidate detection:

```bash
python -m backend.app.cli examples/sample_events.json --output clip_plan.json
```

## Tests

```bash
python -m compileall -q backend tests
python -m unittest discover -s tests -v
```

See [MVP usage](docs/MVP_USAGE.md), [copyright and permissions](docs/COPYRIGHT_POLICY.md), and [system architecture](docs/SYSTEM_ARCHITECTURE.md).

## Rights and safety

Only process footage and data you own or are authorized to use. Game footage, music, and third-party material may have separate rights. This project does not scrape, rip streams, bypass platform controls, or automatically publish. See [Copyright and Permissions](docs/COPYRIGHT_POLICY.md).
