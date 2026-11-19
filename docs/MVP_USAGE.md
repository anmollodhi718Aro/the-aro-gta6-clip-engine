# MVP Usage

The local MVP has two independent steps:

1. Analyze authorized chat/event data and generate a candidate clip plan.
2. Render a clip from a local media file that you own or are authorized to process.

It does not connect to YouTube, download livestream video, synchronize chat/video clocks, or publish content.

## Analyze synthetic chat events

From the repository root:

```bash
python -m backend.app.cli examples/sample_events.json --output clip_plan.json
python -m unittest discover -s tests -v
```

The sample contains synthetic timestamps and events only. The detector uses 10-second windows by default and compares each window with the previous three windows. It marks unusually active windows as candidates. Identical event IDs are counted once; conflicting reuse of an event ID is rejected.

Output candidates are marked `needs_review`. Publishing remains disabled.

## Render an authorized local media file

The clipper accepts local filesystem paths only. It never fetches a URL. It requires an explicit rights confirmation and refuses to overwrite an existing output. FFmpeg renders to a unique temporary file in the destination folder; the completed file is published with an atomic no-overwrite operation. If another render wins the same output path, its file is preserved and the losing render reports a collision.

```python
from backend.app.clipping import render_clip

render_clip(
    "authorized_source.mp4",
    "review_clip.mp4",
    start_seconds=12.0,
    end_seconds=38.0,
    rights_confirmed=True,
)
```

Install FFmpeg separately and make sure the `ffmpeg` executable is on your PATH. Clip offsets are seconds relative to the local media file. Do not convert chat timestamps into media offsets until a reliable clock synchronization offset has been established.

The rights flag is a software guardrail, not legal verification. Creator permission may not clear music, game publisher rights, or other third-party material. Review rights before distribution.
