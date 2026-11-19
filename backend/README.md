# Backend

## Implemented local MVP

- Typed permission, chat-event, and clip-candidate models.
- Permission-gated deterministic chat-spike detection.
- JSON CLI that exports review-only candidate plans.
- Permission-gated local FFmpeg clip rendering from an operator-supplied file.
- Optional 9:16 center crop for Shorts-style output.

## Analyze synthetic chat events

From the repository root:

```bash
python -m backend.app.cli examples/sample_events.json --output clip_plan.json
```

## Render a clip from your own/authorized local recording

Install FFmpeg and ensure both `ffmpeg` and `ffprobe` are available on PATH. Create a permission JSON file:

```json
{
  "source_id": "my-local-recording",
  "granted_by": "your-owner-or-license-attestation",
  "scopes": ["render_video"],
  "granted_at": "2026-11-19T00:00:00+05:30"
}
```

Then run:

```bash
python -m backend.app.clip_cli input.mp4 output.mp4 --start 45 --duration 35 --permission permission.json --confirm-authorized --vertical
```

Remove `--vertical` to preserve the source aspect ratio. The command never downloads footage or publishes clips. It refuses missing/expired/revoked permission, invalid ranges, and existing output files.

## Tests

```bash
python -m compileall -q backend tests
python -m unittest discover -s tests -v
```

Provider integrations, live stream ingestion, a web dashboard, and publishing are not part of this local MVP.
