# YouTube streamList gRPC integration

The optional adapter in backend/app/youtube_stream_list_grpc.py builds the
official protobuf request, opens a TLS gRPC channel to
dns:///youtube.googleapis.com:443, and attaches API-key or OAuth metadata.
The base project remains dependency-free because imports are lazy.

## Setup

Install optional dependencies with pip install -e ".[youtube-stream]".
Obtain Google's official stream_list.proto from the
[Streaming Live Chat guide](https://developers.google.com/youtube/data/live/streaming-live-chat)
and generate modules:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. stream_list.proto
```

Set exactly one runtime environment variable: YOUTUBE_API_KEY or
YOUTUBE_OAUTH_ACCESS_TOKEN. Never commit credentials or paste them into chat.

## Wiring

Call make_stream_factory(), then pass the returned factory to
run_bounded_stream_list(). The adapter sends part=["snippet"], live_chat_id,
and the saved page_token. Convert each response with
response_to_chat_events(response, video_id) and persist through the idempotent
event store before the callback returns.

Each connection owns a TLS channel which closes when the stream iterator
ends. The worker provides bounded reconnect and checkpoint resume. Delivery
is at-least-once, so event persistence must be idempotent.

The adapter handles chat metadata only. It does not fetch video media,
synchronize chat timestamps to footage, or publish content.

Official references:
- https://developers.google.com/youtube/data/live/streaming-live-chat
- https://developers.google.com/youtube/data/live/reference/rest/v3/liveChatMessages/streamList
