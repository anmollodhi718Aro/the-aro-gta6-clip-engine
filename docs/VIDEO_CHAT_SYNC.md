# Video and Chat Clock Synchronization

This module maps already-detected chat candidate timestamps to offsets in a supplied
video file. It requires an explicit operator-measured clock offset. It does not
infer synchronization from chat volume, inspect video frames, or claim AI detection.

## Offset convention

The convention is:

`video_time = chat_time + offset_seconds`

The caller supplies a timezone-aware video epoch and a timezone-aware chat timestamp.
The resulting position is measured in seconds from the supplied video epoch.

## Example

```python
from datetime import datetime, timezone
from backend.app.models import CandidateMoment
from backend.app.video_chat_sync import ClockOffset, candidate_to_video_window

origin = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
offset = ClockOffset(
    offset_seconds=5.0,
    measured_by="operator",
    measured_at=origin,
    uncertainty_seconds=0.5,
)
# Pass an existing CandidateMoment and the actual video duration.
window = candidate_to_video_window(
    candidate, origin, offset, video_duration_seconds=1800
)
print(window.to_dict())
```

All mapped windows retain `needs_review`. The module rejects negative positions,
invalid durations, and windows extending beyond the supplied video duration.
An uncertainty above two seconds is labeled low confidence. The offset must be
measured using a shared event visible in both clocks; it is never guessed.
