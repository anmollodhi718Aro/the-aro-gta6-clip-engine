# Local media probe and batch review rendering

The batch workflow accepts a JSON manifest containing a local media path, the UTC timestamp corresponding to the beginning of that file, a measured clock synchronization record, and detector candidate objects.

The media probe calls ffprobe with an argument array and reads the file duration and format. It does not accept network URLs. The batch renderer converts each candidate using the measured chat-minus-media offset, clamps against the probed duration, and sends each clip to the existing FFmpeg renderer. Rights confirmation is required explicitly on the CLI.

Example manifest shape:

{
  "media_path": "authorized_capture.mp4",
  "media_start_utc": "2026-11-19T10:00:00+00:00",
  "clock_sync": {
    "chat_minus_media_seconds": 0.42,
    "uncertainty_seconds": 0.15,
    "measured_at": "2026-11-19T10:05:00+00:00",
    "method": "documented synchronization slate"
  },
  "candidates": [
    {
      "source_id": "authorized-source",
      "peak_window_start": "2026-11-19T10:02:10+00:00",
      "clip_start": "2026-11-19T10:01:55+00:00",
      "clip_end": "2026-11-19T10:02:25+00:00",
      "peak_message_count": 12,
      "baseline_average": 2.0,
      "score": 90,
      "explanation": "example candidate"
    }
  ]
}

Run from the repository root:

python -m backend.app.batch_render manifest.json --output-dir review_clips --confirm-rights

The resulting review_manifest.json records rendered paths, mapped time bounds, failures, and needs_review status. Existing outputs are skipped rather than overwritten. Publishing remains disabled. The sample offset and timestamps are illustrative; replace them with measured synchronization and actual media metadata.
