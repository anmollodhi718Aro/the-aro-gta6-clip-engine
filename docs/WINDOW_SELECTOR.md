# Review Window Selector

The selector ranks **already-detected and time-mapped** chat candidates. It is a
deterministic review aid, not an AI video understanding system.

## Policy

- Rank by existing detector score, then peak chat count.
- Reject windows longer than the local renderer's 180-second limit.
- Enforce a configurable minimum gap between selected windows.
- Enforce maximum clip count and total selected duration.
- Return selected windows in chronological order.
- Every result remains `needs_review`, with `human_review_required=true` and
  `render_approved=false`.

The selector does not inspect frames/audio, infer what happened in GTA gameplay,
or approve rendering or publishing. The operator must review the actual recording,
rights, context, and timing.

## Python use

```python
from backend.app.window_selector import SelectionPolicy, select_review_windows

selected = select_review_windows(
    candidates,
    mapped_windows,
    SelectionPolicy(max_clips=5, min_gap_seconds=5, max_total_duration_seconds=300),
)
```

The candidates and mapped windows must be in corresponding input order, with
matching source IDs. Mapping must use an operator-measured synchronization offset.
