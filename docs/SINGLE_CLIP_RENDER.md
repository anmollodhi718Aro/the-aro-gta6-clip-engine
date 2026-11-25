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

The low-level renderer also rejects boolean clip bounds explicitly. Python treats booleans as integers, so values such as `True` must not silently become a one-second timestamp when the helper is called directly. The output is rendered locally through the existing collision-safe FFmpeg helper, then checked again with FFprobe. A successful render is still only a local artifact and requires manual playback/review. This command does not authenticate, upload, schedule, or publish.

Use only a source file that the owner has explicitly authorized for this processing scope. The confirmation flag is a workflow guardrail, not independent legal verification. Never use this command with scraped, ripped, or otherwise unapproved third-party media.


## Source snapshot safety

Before preflight, the CLI opens the one selected source without following symlinks where the platform supports `O_NOFOLLOW`, verifies that the opened descriptor and selected pathname identify the same regular file, and copies the source to a private temporary snapshot in bounded 1 MiB chunks. It rechecks descriptor metadata and pathname identity after the copy and rejects partial, replaced, or mutated sources. FFprobe and FFmpeg both consume that same snapshot, so the source bytes rendered are the bytes that passed preflight. The temporary snapshot is removed when the invocation ends. This uses temporary disk space proportional to the selected source size; it does not buffer the video in RAM or enumerate other files.


## Dry-run and rights-confirmation storage boundary

A dry-run probes the one selected source in place and does not create a duplicate video snapshot. If `--execute` is supplied without `--confirm-rights`, the command returns `BLOCKED` before opening or copying the source. Only an explicitly confirmed execution creates the private descriptor-verified snapshot used by both FFprobe and FFmpeg. The snapshot still uses temporary disk space proportional to the selected source size; it is not created for planning-only runs.
