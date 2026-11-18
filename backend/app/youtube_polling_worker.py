"""Bounded, permission-rechecking YouTube live-chat polling worker."""
from __future__ import annotations
import math, threading, time
from dataclasses import dataclass
from typing import Callable
from .consent_registry import ConsentRegistry
from .youtube_live_chat import YouTubeChatBatch, YouTubeLiveChatClient

@dataclass(frozen=True)
class PollingResult:
    batches_fetched: int
    events_received: int
    stopped_by_request: bool
    last_page_token: str | None

def run_bounded_polling(*, client: YouTubeLiveChatClient, registry: ConsentRegistry,
                        video_id: str, on_batch: Callable[[YouTubeChatBatch], None],
                        stop_event: threading.Event, max_batches: int,
                        max_runtime_seconds: float, wait: Callable[[float], bool] | None = None,
                        monotonic: Callable[[], float] = time.monotonic) -> PollingResult:
    """Poll within explicit limits. wait(seconds) returns True if stop interrupted it.

    Permission/API errors propagate. No silent retries occur after a failed check.
    """
    if not video_id.strip(): raise ValueError("video_id is required")
    if not callable(on_batch): raise ValueError("on_batch callback is required")
    if max_batches < 1 or max_batches > 10000:
        raise ValueError("max_batches must be between 1 and 10000")
    if not math.isfinite(max_runtime_seconds) or not 0 < max_runtime_seconds <= 86400:
        raise ValueError("max_runtime_seconds must be greater than 0 and at most 86400")
    wait_fn = wait or stop_event.wait
    deadline = monotonic() + max_runtime_seconds
    page_token = None
    live_chat_id = None
    batches = events = 0
    while batches < max_batches and not stop_event.is_set():
        remaining = deadline - monotonic()
        if remaining <= 0: break
        permission = registry.require(video_id, "analyze_chat")
        batch = client.fetch_recent_messages(video_id, permission,
            live_chat_id=live_chat_id, page_token=page_token)
        on_batch(batch)
        batches += 1
        events += len(batch.events)
        live_chat_id = batch.live_chat_id
        page_token = batch.next_page_token
        if batch.offline or batches >= max_batches: break
        interval_ms = batch.polling_interval_ms or 5000
        delay = max(1.0, interval_ms / 1000.0)
        remaining = deadline - monotonic()
        if remaining <= 0: break
        if wait_fn(min(delay, remaining)): break
    return PollingResult(batches, events, stop_event.is_set(), page_token)