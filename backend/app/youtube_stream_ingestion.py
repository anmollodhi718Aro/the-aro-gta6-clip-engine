"""Glue official streamList protobuf responses to durable event storage."""
from __future__ import annotations
from typing import Any, Callable
from .chat_event_store import ChatEventStore, IngestionResult
from .youtube_stream_list_grpc import response_to_chat_events

def make_durable_response_handler(*, video_id: str, event_store: ChatEventStore,
                                  on_ingested: Callable[[IngestionResult], None] | None = None):
    """Return a worker callback that commits converted events before returning.

    The stream worker advances its page-token checkpoint only after this
    callback returns. ChatEventStore provides event-level idempotency.
    """
    if not isinstance(video_id, str) or not video_id.strip():
        raise ValueError("video_id is required")
    if not isinstance(event_store, ChatEventStore):
        raise TypeError("event_store must be a ChatEventStore")
    def handle(response: Any) -> None:
        events = response_to_chat_events(response, video_id)
        result = event_store.persist(events)
        if on_ingested is not None:
            on_ingested(result)
    return handle
