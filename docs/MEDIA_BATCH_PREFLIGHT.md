# Multi-video inventory preflight

The first phase of the batch workflow reviews the complete local video folder before any rendering starts.

Run a recursive, read-only inventory:

```bash
python -m backend.app.media_batch_preflight "/path/to/authorized-recordings" --output reports/media_inventory.json
```

Use `--top-level-only` to skip subfolders. The command considers common video extensions, rejects symbolic-link inputs, and calls FFprobe for every discovered candidate. A file receives PASS only when FFprobe returns a finite positive duration and at least one video stream. The report records relative path, size, duration, container format, video codec and dimensions, plus an individual error for each failed file. One bad file does not stop inspection of the remaining files.

The report is created exclusively: an existing report path is never overwritten. Exit codes are 0 when every discovered video passes, 1 when one or more files or directory traversal operations fail, and 2 when the inventory itself cannot start or its report cannot be written.

## Processing gate

This command does not render, upload, publish, delete, or modify media. It only prepares the review report. Human review and source-rights confirmation remain required. Batch rendering is a separate later phase; do not treat a PASS inventory result as permission to process or publish a file.

`files_discovered` counts supported video candidates, not unrelated files. `processing_started` and `publishing_enabled` are always false in this report.
