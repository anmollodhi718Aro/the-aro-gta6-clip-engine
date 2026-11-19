# MVP Usage

The local MVP has two independent workflows: chat-event analysis and video rendering. Neither workflow downloads content or publishes automatically.

## 1. Analyze chat activity

Create a JSON file containing a permission record and event list. The permission must include `analyze_chat`, and each event must belong to the same source. Timestamps must include a timezone.

Run from the repository root:

```bash
python -m backend.app.cli examples/sample_events.json --output clip_plan.json
```

The detector uses 10-second windows by default, compares each window with the previous three windows, and marks unusual activity as candidates. Results are review-only.

## 2. Render a video clip

Use a local video file that you own or are licensed/otherwise authorized to process. Install FFmpeg and ensure `ffmpeg` and `ffprobe` are available on PATH.

Create `permission.json`:

```json
{
  "source_id": "my-recording",
  "granted_by": "owner-or-license-attestation",
  "scopes": ["render_video"],
  "granted_at": "2026-11-19T00:00:00+05:30"
}
```

Render a 35-second vertical clip beginning at 45 seconds:

```bash
python -m backend.app.clip_cli recording.mp4 output/clip-001.mp4 --start 45 --duration 35 --permission permission.json --confirm-authorized --vertical
```

Omit `--vertical` to preserve the source aspect ratio. The tool refuses to proceed without the explicit `--confirm-authorized` flag and a currently valid `render_video` permission. It checks the source duration, limits each render to 600 seconds, and will not overwrite an existing output file.

The permission JSON is an operator attestation, not independent legal verification. You remain responsible for having rights to the video, game footage, audio, and any third-party material. Do not use stream-ripping, scraping, or platform-control bypasses.

## 3. Run tests

```bash
python -m compileall -q backend tests
python -m unittest discover -s tests -v
```

Publishing, live monitoring, automatic highlight detection from video/audio, and a dashboard remain future milestones. Review and publish manually.
