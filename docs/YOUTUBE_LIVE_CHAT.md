# YouTube Live Chat Adapter

## Current adapter scope

`backend/app/youtube_live_chat.py` implements a read-only, one-page-at-a-time adapter for publicly accessible YouTube livestream chat. `backend/app/youtube_cli.py` connects one fetched page to the chat-spike detector and writes a review-only JSON plan.

It:
- finds a currently active chat using `videos.list` and `liveStreamingDetails.activeLiveChatId`
- retrieves one bounded page using `liveChatMessages.list`
- exposes the API-provided `nextPageToken` and `pollingIntervalMillis`
- checks the source permission record before making a chat request
- stores only message ID, source video ID, timestamp, and display text
- does not implement chat posting, moderation, stream downloading, or video acquisition

## Setup

1. Create an eligible Google Cloud project and enable YouTube Data API v3.
2. Create an API key restricted to the YouTube Data API and suitable application restrictions.
3. Set `YOUTUBE_API_KEY` as an environment variable on the machine running the adapter.
4. Create a local SQLite consent registry and record the creator grant, or use the JSON fallback below. Registry example:

```json
{
  "source_id": "YOUR_VIDEO_ID",
  "granted_by": "creator-handle",
  "scopes": ["analyze_chat"],
  "granted_at": "2026-11-18T00:00:00+00:00",
  "expires_at": "2026-11-19T00:00:00+00:00"
}
```

5. Run one bounded request using the registry (recommended for the local MVP):

```bash
python -m backend.app.youtube_cli YOUR_VIDEO_ID --registry data/consent.sqlite3 --output youtube_clip_plan.json
```

Alternatively, run with the legacy JSON permission file:

```bash
python -m backend.app.youtube_cli YOUR_VIDEO_ID --permission permission.json --output youtube_clip_plan.json
```

6. If the output contains a `next_page_token`, wait at least the returned `polling_interval_ms`, then pass both `--live-chat-id` and `--page-token` to request the next page. Do not poll more frequently than YouTube specifies.

Never commit the permission file if it contains personal or confidential information. Never commit the API key or paste it into chat.

## Quota and latency

Each `videos.list` call costs 1 quota unit and each `liveChatMessages.list` call costs 5 units according to the official API reference. Keep page requests bounded and honor `pollingIntervalMillis`. The official documentation recommends `liveChatMessages.streamList` for continuous low-latency ingestion; the current REST adapter is a finite polling fallback, not the final always-on worker.

## Important timestamp limitation

The chat event timestamps are not video offsets. The output intentionally does not automatically render clips from these timestamps. A measured clock synchronization offset and an authorized local video asset are required first.

## Official references

- [Videos: list](https://developers.google.com/youtube/data/reference/rest/v3/videos)
- [LiveChatMessages: list](https://developers.google.com/youtube/data/live/reference/rest/v3/liveChatMessages/list)
- [LiveChatMessages: streamList](https://developers.google.com/youtube/data/live/reference/rest/v3/liveChatMessages/streamList)
- [Streaming Live Chat guide](https://developers.google.com/youtube/data/live/streaming-live-chat)
