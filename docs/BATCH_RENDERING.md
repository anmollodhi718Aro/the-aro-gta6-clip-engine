# Human-Approved Batch Rendering

This command turns rows from the measured clip candidate CSV into local render jobs. It does not fetch video, upload files, or publish content.

## 1. Create a measured candidate pack

Follow [Measured Clip Candidate Pack](CLIP_CANDIDATE_PACK.md). The candidate CSV must map to the exact local recording being processed.

## 2. Dry-run selected rows

From the repository root:

```bash
python -m backend.app.batch_render clip_pack/clip_candidates.csv \
  --media "/path/to/authorized-local-recording.mp4" \
  --approve 1,3 \
  --output-dir rendered_clips
```

The command is dry-run by default. It writes a JSON report and does not invoke FFmpeg. Each run gets its own folder under the output root; omit `--run-id` to generate a unique ID. A supplied run ID must be a safe 1-64 character name.

Row numbers are the 1-based positions in the CSV, excluding the header. Inspect the CSV and report, then approve only the exact rows you reviewed.

## 3. Execute approved local renders

Only after reviewing the exact source and selected rows:

```bash
python -m backend.app.batch_render clip_pack/clip_candidates.csv \
  --media "/path/to/authorized-local-recording.mp4" \
  --approve 1,3 \
  --output-dir rendered_clips \
  --execute \
  --confirm-rights
```

Both `--execute` and `--confirm-rights` are required for rendering. The rights confirmation applies to the exact local media file supplied. This is an engineering guardrail, not legal verification.

## 4. Retry only failed rows

A previous report can be used to select failed rows without re-running successful, blocked, or unapproved candidates:

```bash
python -m backend.app.batch_render clip_pack/clip_candidates.csv \
  --media "/path/to/authorized-local-recording.mp4" \
  --retry-report rendered_clips/previous-run/batch_render_report.json \
  --output-dir rendered_clips
```

This is a dry-run. To execute the retry, add `--execute --confirm-rights` after reviewing the failed-row selection and confirming authorization for the exact local media file. The retry creates a new run folder, never reuses the previous run's output paths, and retries only rows whose source ID and measured start/end bounds still match the current candidate CSV. Older reports without recorded bounds are rejected rather than guessed.

## Safeguards

- Only local filesystem media paths are accepted; remote URLs are not supported.
- Every candidate must be explicitly selected by its 1-based CSV row number, or selected from a prior report's failed rows with `--retry-report`.
- Candidates marked non-renderable are blocked even if selected.
- Invalid, negative, non-finite, or over-limit time bounds are rejected.
- Every execution creates a new run folder and refuses to reuse an existing folder. Use a new `--run-id` for another attempt.
- JSON reports are written through a sibling temporary file and atomically replaced.
- FFmpeg's existing no-overwrite behavior is preserved.
- A JSON report records planned, rendered, blocked, skipped, or failed rows. Failed-row retries do not select successful, blocked, or unapproved rows.
- Rendering never implies approval to distribute. Human review and all applicable rights checks remain necessary.
- No upload, publishing, stream downloading, or scraping is implemented.
