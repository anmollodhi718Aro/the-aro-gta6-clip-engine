# YouTube Live Chat Adapter

## Current adapter scope

`backend/app/youtube_live_chat.py` implements a **read-only, one-page-at-a-time** adapter for publicly accessible YouTube livestream chat.

It:
- finds a currently active chat using `videos.list` and `liveStreamingDetails.activeLiveChatId`
- retrieves one bounded page using `liveChatMessages.list`
- uses the API-provided `nextPageToken` and `pollingIntervalMillis` so a future worker can resume responsibly
- checks the source permission record before making a chat request
- stores only message ID, source video ID, timestamp, and display text
- does not implement chat posting, moderation, stream downloading, or video acquisition

## Quota and latency

Each `videos.list` call costs 1 quota unit and each `liveChatMessages.list` call costs 5 units according to the current official API reference. Keep page requests bounded and honor `pollingIntervalMillis`. The official documentation recommends `liveChatMessages.streamList` for continuous low-latency ingestion; the current REST adapter is a finite polling fallback, not the final always-on worker.

## Setup

1. Create an eligible Google Cloud project and enable YouTube Data API v3.
2. Create an API key restricted to the YouTube Data API and suitable application restrictions.
3. Set `YOUTUBE_API_KEY` as an environment variable on the machine running the adapter.
4. Never commit the key or paste it into chat, issues, or source files.
5. Use only public live chat and only after recording creator permission for analysis and clipping workflow.

The account owner must complete Google account, project, and API authorization steps. Do not bypass age, account, or platform eligibility requirements.

## Official references

- [Videos: list](https://developers.google.com/youtube/data/reference/rest/v3/videos)
- [LiveChatMessages: list](https://developers.google.com/youtube/data/live/reference/rest/v3/liveChatMessages/list)
- [LiveChatMessages: streamList](https://developers.google.com/youtube/data/live/reference/rest/v3/liveChatMessages/streamList)
- [Streaming Live Chat guide](https://developers.google.com/youtube/data/live/streaming-live-chat)

## Known gap

The adapter is not yet connected to the detector CLI or a continuous queue worker. It returns a typed batch so the next milestone can connect it to the permission-gated detector without changing the detector core.
