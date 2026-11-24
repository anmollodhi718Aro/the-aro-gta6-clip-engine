# MVP Usage

The MVP analyzes a JSON file of chat events and can render a short, local review clip from a video file you own or are explicitly authorized to edit. It does not connect to YouTube, download platform video, or publish content.

## Analyze chat events

Create a JSON file with a permission record and event list:

```json
{
  "permission": {
    "source_id": "sample-stream",
    "granted_by": "creator-handle",
    "scopes": ["analyze_chat"],
    "granted_at": "2026-11-18T00:00:00+00:00",
    "expires_at": "2026-11-19T00:00:00+00:00"
  },
  "events": [
    {
      "event_id": "event-001",
      "source_id": "sample-stream",
      "timestamp": "2026-11-18T12:00:01+00:00",
      "text": "synthetic sample"
    }
  ]
}
```

Use only data you are allowed to process. The example timestamps and text are synthetic.

```bash
python -m backend.app.cli sample_events.json --output clip_plan.json
```

The detector uses 10-second windows by default, compares each window with the previous three windows, and marks unusually active windows as candidates. Output candidates are marked `needs_review`.

## Render an authorized local clip

Install FFmpeg and ensure `ffmpeg` is available on PATH. Then run:

```bash
python -m backend.app.render_cli input_video.mp4 review_clip.mp4 --start 12.5 --duration 35 --confirm-rights
```

The command requires the explicit `--confirm-rights` flag, limits clips to 180 seconds, refuses to overwrite an existing output, and writes a local MP4 for human review. It never downloads or uploads media. Review the clip and verify all applicable creator, game, music, guest, and platform rights before any separate distribution decision.

## Tests

```bash
python -m unittest discover -s tests -v
```

CI installs FFmpeg and FFprobe and runs a synthetic-video export test. Publishing is not implemented and remains disabled.
