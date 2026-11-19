# Measured Clock Synchronization

The clip engine must never assume that a chat timestamp is also a video-file
position. Chat ingestion and a local recording can start at different times,
and their clocks can drift.

## Calibration input

An operator must identify at least three synchronization markers that can be
matched in both the authorized chat timeline and the local recording. Record
each pair as:

- \`source_id\`: the same stream/source identifier for every anchor
- \`chat_time\`: an ISO-8601 timestamp with an explicit timezone
- \`media_seconds\`: the marker's measured position in the local recording

Do not fabricate anchors or infer them from the chat spike itself. The markers
must be independently recognizable in both timelines.

## Fit and validate

\`backend.app.clock_sync.fit_clock_sync\` fits a linear mapping from chat elapsed
seconds to local-media seconds. It rejects:

- fewer than three anchors or anchors from different sources
- duplicate or non-increasing chat times or media positions
- excessive maximum anchor residual (default 1 second)
- excessive clock drift (default 1,000 ppm)

The resulting \`ClockSync.map_chat_time\` only maps timestamps between the first
and last calibration anchors. It refuses extrapolation beyond the measured
interval. A successful fit is a calibration aid, not proof that a candidate
is interesting or that media rights are cleared.

## Example

\`\`\`python
from datetime import datetime, timezone
from backend.app.clock_sync import ClockAnchor, fit_clock_sync

anchors = [
    ClockAnchor("authorized-stream-1", datetime.fromisoformat("2026-01-01T12:00:00+00:00"), 8.4),
    ClockAnchor("authorized-stream-1", datetime.fromisoformat("2026-01-01T12:01:00+00:00"), 68.4),
    ClockAnchor("authorized-stream-1", datetime.fromisoformat("2026-01-01T12:02:00+00:00"), 128.4),
]
sync = fit_clock_sync(anchors)
media_position = sync.map_chat_time(
    datetime(2026, 1, 1, 12, 1, 30, tzinfo=timezone.utc)
)
\`\`\`

Run the focused tests with:

\`\`\`bash
python -m unittest discover -s tests -p "test_clock_sync.py" -v
\`\`\`

The feature does not fetch, download, or publish video. Existing human review
and rights-confirmation requirements remain unchanged.
