# Measured Clip Candidate Pack

The analysis CLI produces UTC chat timestamps. They must not be treated as video offsets directly.

Once the operator has a local recording they are authorized to process and has measured the UTC timestamp corresponding to media offset zero, create a review pack:

```bash
python -m backend.app.clip_pack youtube_clip_plan.json \
  --media-origin-utc "2026-11-19T12:00:00+00:00" \
  --output-dir clip_pack
```

Replace the example timestamp with the measured origin for that exact recording. Do not guess it from the livestream start time or a displayed clock. If the offset has not been measured, stop before mapping.

The command writes:

- `clip_candidates.csv`: sortable edit notes with media-relative start/end seconds.
- `clip_candidates.md`: compact human review sheet.

Candidates that start before the recording, end before it, or exceed the local renderer's 180-second limit are marked not renderable. No video is downloaded, rendered, uploaded, or published by this command. The CSV is not an approval to publish. Review source consent, context, and game/music/third-party rights before editing or distribution.

## Output safety

The exporter stages both the CSV and Markdown review files, then publishes them without replacing existing files. If either output already exists, choose a new `--output-dir`; existing review decisions are preserved. If a concurrent export claims one of the two filenames during publication, any file created by the losing export is rolled back.
