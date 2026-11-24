"""Permission-gated event normalization and deduplication."""
from __future__ import annotations
from datetime import timezone
from typing import Any, Iterable
from .models import ChatEvent, PermissionRecord
MAX_EVENT_BATCH=10_000
MAX_EVENT_TEXT_LENGTH=4_000

def normalize_event_batch(records:Iterable[dict[str,Any]],permission:PermissionRecord,
                          *,max_events:int=MAX_EVENT_BATCH,
                          max_text_length:int=MAX_EVENT_TEXT_LENGTH)->list[ChatEvent]:
    if max_events<=0 or max_text_length<0: raise ValueError("event/text limits are invalid")
    raw=list(records)
    if len(raw)>max_events: raise ValueError(f"event batch exceeds {max_events}")
    unique={}
    for item in raw:
        if not isinstance(item,dict): raise TypeError("event must be an object")
        if "timestamp" not in item: raise ValueError("event timestamp is required")
        if "text" in item and not isinstance(item["text"],str): raise TypeError("event text must be a string")
        event=ChatEvent.from_dict(item)
        if len(event.text)>max_text_length: raise ValueError("event text exceeds configured limit")
        if event.source_id!=permission.source_id: raise ValueError("event source mismatch")
        if not permission.allows("analyze_chat",event.timestamp):
            raise PermissionError("active analyze_chat permission is required")
        event=ChatEvent(event.event_id,event.source_id,event.timestamp.astimezone(timezone.utc),event.text)
        previous=unique.get(event.event_id)
        if previous is not None and previous!=event: raise ValueError("conflicting duplicate event_id")
        unique[event.event_id]=event
    return sorted(unique.values(),key=lambda e:(e.timestamp,e.event_id))
