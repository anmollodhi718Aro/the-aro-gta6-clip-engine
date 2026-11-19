# Official YouTube streamList worker

The core worker in backend/app/youtube_stream_list_worker.py consumes the
official server-streaming liveChatMessages.streamList interface through an
injected generated gRPC stub. It does not bundle generated protobuf code or
force gRPC dependencies into the stdlib-only core package.

## Integration contract

1. Obtain the active liveChatId using the official YouTube Data API and an
   authorized API key or OAuth access token.
2. Generate the official client from Google's documented stream_list.proto.
3. Build stream_factory(live_chat_id, page_token) to create the
   V3DataLiveChatMessageServiceStub.StreamList(request, metadata=...) iterator.
   Include the required part and live_chat_id request fields.
4. Pass a durable, idempotent on_response(response) callback. It must return
   only after the response messages have been persisted.
5. Run with explicit response/runtime/reconnect limits and a stop event.

The worker restores the last page token from SQLite, rechecks creator consent
before each connection and reconnect, and advances its checkpoint only after
the callback succeeds. Processing is at-least-once: a crash between callback
commit and checkpoint commit can replay a response. Event-level idempotency
is required.

## Recovery behavior

- Retries only gRPC UNAVAILABLE, DEADLINE_EXCEEDED, and RESOURCE_EXHAUSTED
  statuses, using bounded exponential backoff.
- Does not retry permission, invalid-argument, ended/disabled-chat, or unknown
  failures. These are surfaced to the caller.
- A normal iterator end is treated as a disconnect and resumed from the last
  checkpoint, within reconnect and runtime limits.
- Stops on request, offline marker, response limit, runtime deadline, or
  reconnect limit.
- Authentication metadata is owned by the injected integration layer.

## Important limits

The generated stub and credentials are not constructed by this module. The
application must supply them using Google's official sample/proto contract.
The worker processes chat metadata only; it does not access or download video.
It does not establish a chat-to-video clock offset. Creator permission does
not automatically clear game publisher, music, or third-party rights.

## Official references

- https://developers.google.com/youtube/data/live/reference/rest/v3/liveChatMessages/streamList
- https://developers.google.com/youtube/data/live/streaming-live-chat
