# Calibrated Clip Candidate Pack

The clip pack consumes the measured clock calibration module. It does not use
a guessed media-origin timestamp and does not treat chat time as media offset.

## Calibration JSON

Create a JSON file with at least three independently measured markers from the
same authorized stream and the exact local recording:

```json
{
  "anchors": [
    {"source_id": "stream-a", "chat_time": "2026-11-19T12:00:00+00:00", "media_seconds": 8.0},
    {"source_id": "stream-a", "chat_time": "2026-11-19T12:01:00+00:00", "media_seconds": 68.0},
    {"source_id": "stream-a", "chat_time": "2026-11-19T12:02:00+00:00", "media_seconds": 128.0}
  ]
}
```

The markers must be recognizable in both timelines. Do not estimate or invent
them. The fit validates source identity, monotonicity, drift, and residuals,
and only maps within the first and last measured anchors.

## Run

```bash
python -m backend.app.clip_pack candidate_plan.json --calibration calibration.json --output-dir clip_pack
```

The candidate plan must contain a `candidates` array with source_id,
clip_start, and clip_end. The command writes CSV and Markdown review notes
without overwriting existing files. It does not download, render, upload, or
publish media. Human review and rights confirmation remain mandatory.

Run focused tests:

```bash
python -m unittest discover -s tests -p "test_calibrated_clip_pack.py" -v
```
