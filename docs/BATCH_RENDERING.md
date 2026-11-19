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

The command is dry-run by default. It writes a JSON report and does not invoke FFmpeg.

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

## Safeguards

- Only local filesystem media paths are accepted; remote URLs are not supported.
- Every candidate must be explicitly selected by its 1-based CSV row number.
- Candidates marked non-renderable are blocked even if selected.
- Invalid, negative, non-finite, or over-limit time bounds are rejected.
- FFmpeg's existing no-overwrite behavior is preserved.
- A JSON report records planned, rendered, blocked, skipped, or failed rows.
- Rendering never implies approval to distribute. Human review and all applicable rights checks remain necessary.
- No upload, publishing, stream downloading, or scraping is implemented.
