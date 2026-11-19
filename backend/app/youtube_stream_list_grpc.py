"""Optional official gRPC transport adapter for YouTube streamList."""
from __future__ import annotations
import os
from collections.abc import Iterator
from typing import Any

GRPC_TARGET = "dns:///youtube.googleapis.com:443"

def make_stream_factory(*, api_key: str | None = None, oauth_token: str | None = None,
                        grpc_module: Any | None = None, messages_module: Any | None = None,
                        services_module: Any | None = None):
    """Build a stream factory; credentials and generated modules are injected/lazy."""
    key = api_key or os.getenv("YOUTUBE_API_KEY")
    token = oauth_token or os.getenv("YOUTUBE_OAUTH_ACCESS_TOKEN")
    if bool(key) == bool(token):
        raise ValueError("Set exactly one of YOUTUBE_API_KEY or YOUTUBE_OAUTH_ACCESS_TOKEN")
    if grpc_module is None:
        try:
            import grpc as grpc_module
        except ImportError:
            raise RuntimeError("Install the youtube-stream optional dependencies for gRPC") from None
    if messages_module is None or services_module is None:
        try:
            import stream_list_pb2 as generated_messages
            import stream_list_pb2_grpc as generated_services
        except ImportError:
            raise RuntimeError("Generate the official stream_list protobuf Python modules first") from None
        messages_module = messages_module or generated_messages
        services_module = services_module or generated_services
    metadata = (("x-goog-api-key", key),) if key else (("authorization", "Bearer " + token),)
    tls = grpc_module.ssl_channel_credentials()
    def stream_factory(live_chat_id: str, page_token: str | None) -> Iterator[Any]:
        if not isinstance(live_chat_id, str) or not live_chat_id.strip():
            raise ValueError("live_chat_id is required")
        request = messages_module.LiveChatMessageListRequest(
            part=["snippet"], live_chat_id=live_chat_id, page_token=page_token or "")
        with grpc_module.secure_channel(GRPC_TARGET, tls) as channel:
            stub = services_module.V3DataLiveChatMessageServiceStub(channel)
            yield from stub.StreamList(request, metadata=metadata)
    return stream_factory

def response_to_chat_events(response: Any, video_id: str) -> tuple:
    """Convert text-bearing protobuf chat items into validated ChatEvent objects."""
    from .models import ChatEvent
    events = []
    for item in getattr(response, "items", ()):
        snippet = getattr(item, "snippet", None)
        if snippet is None:
            continue
        event_id = getattr(item, "id", "")
        published_at = getattr(snippet, "published_at", "")
        message = getattr(snippet, "display_message", "")
        if event_id and published_at and message:
            events.append(ChatEvent(event_id=str(event_id), source_id=video_id,
                timestamp=str(published_at), text=str(message)))
    return tuple(events)
