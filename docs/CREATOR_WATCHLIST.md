# Seven-day GTA creator watchlist

The watchlist is a candidate list, not a claim that every creator is currently streaming GTA 6. Creator identity, current game category, and live status must be checked against current public sources before reporting results.

## Run

```bash
python -m backend.app.creator_watchlist_cli examples/creator_metrics.example.json --output output/creator_ranking.json
```

Input is a JSON object with a `metrics` array. Every row must contain:
- `creator_id`: one ID from the watchlist
- `window_start` and `window_end`: ISO-8601 timestamps with timezone offsets, exactly seven days apart
- `views` and `live_streams`: nonnegative integers
- `source_url`: HTTPS evidence URL

Optional values are `peak_concurrent_viewers`, `average_concurrent_viewers`, and `captured_at`.

The ranking sorts by seven-day views, then peak concurrent viewers, then average concurrent viewers. Missing creators are omitted rather than assigned invented zeroes. Ties after those fields are resolved by creator ID for stable output.

## Candidate identity correction

The requested display name is **Death Tracks Gaming**, with the internal ID `death-tracks-gaming`. **Death Rush Gaming** remains a separate candidate.

## Boundaries

- Metrics must be supplied from evidence-backed, permitted sources. This CLI does not scrape channels or download videos.
- Candidate names and IDs do not prove that a channel belongs to a particular creator.
- Ranking is historical activity, not a prediction of virality.
- Media download and publishing remain disabled. A ranking is not permission to reuse a creator's content.
