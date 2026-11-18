# MVP Usage

The first local milestone analyzes a JSON file of chat events. It does not connect to YouTube, download video, render clips, or publish content.

## Input format

Create a JSON file with a permission record and event list:

```json
{
  "permission": {
    "source_id": "sample-stream",
    "granted_by": "creator-handle",
    "scopes": ["analyze_chat"],
    "granted_at": "2026-11-18T00:00:00+00:00",
    "expires_at": "2026-11-19T00:00:00+00:00"
  },
  "events": [
    {
      "event_id": "event-001",
      "source_id": "sample-stream",
      "timestamp": "2026-11-18T12:00:01+00:00",
      "text": "synthetic sample"
    }
  ]
}
```

Use only data you are allowed to process. The example timestamps and text are synthetic.

## Run

From the repository root:

```bash
python -m backend.app.cli sample_events.json --output clip_plan.json
python -m unittest discover -s tests -v
```

The detector uses 10-second windows by default, compares each window with the previous three windows, and marks unusually active windows as candidates. Tune the parameters only after validating them on representative, permitted data.

Output candidates are marked `needs_review`. Publishing is not implemented and remains disabled.
