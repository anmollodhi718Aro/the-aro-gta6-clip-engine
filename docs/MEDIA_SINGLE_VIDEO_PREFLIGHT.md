# Single-video preflight

This is the required first gate for the owner-selected video. It accepts exactly one file path and never scans a directory or processes a second file.

Run:

```bash
python -m backend.app.media_single_preflight "/path/to/one-authorized-video.mp4" --output reports/selected-video-preflight.json
```

The command checks the selected file's existence, supported video extension, regular-file status, non-zero size, FFprobe duration, container format, video codec and dimensions. A PASS requires valid FFprobe JSON, a finite positive duration, and at least one video stream. Malformed metadata, non-object stream entries, symlinks, and file replacement or ordinary mutation detected during inspection fail closed.

The report is created exclusively so an earlier report cannot be overwritten. This step is read-only. It does not render, transcode, authenticate with Google, upload, publish, or modify the selected video. A PASS means only that the selected file passed metadata preflight. Human review and exact-source rights confirmation remain separate gates. The next file must be selected explicitly in a separate invocation.
