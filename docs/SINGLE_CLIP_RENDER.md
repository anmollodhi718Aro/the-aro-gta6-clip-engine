# One-selected-video clip render

This command is the single-file rendering stage after the owner-selected source passes FFprobe metadata preflight. It never scans a directory or processes multiple videos.

Dry-run (default):

```bash
python -m backend.app.single_clip_render "/path/to/one-authorized-video.mp4" --start 12.5 --end 27.0
```

The command validates the selected source, checks finite clip bounds, enforces the 180-second renderer limit, and confirms that the end time does not exceed the selected video's probed duration. Before inspecting or rendering media, it reserves the JSON report path exclusively. If the report already exists, or aliases the selected source/output path, the command stops before processing. The report is never overwritten. A `PLANNED` result does not create a video.

Actual local rendering requires both explicit flags:

```bash
python -m backend.app.single_clip_render "/path/to/one-authorized-video.mp4" --start 12.5 --end 27.0 --execute --confirm-rights
```

The output is rendered locally through the existing collision-safe FFmpeg helper, then checked again with FFprobe. A successful render is still only a local artifact and requires manual playback/review. This command does not authenticate, upload, schedule, or publish.

Use only a source file that the owner has explicitly authorized for this processing scope. The confirmation flag is a workflow guardrail, not independent legal verification. Never use this command with scraped, ripped, or otherwise unapproved third-party media.
