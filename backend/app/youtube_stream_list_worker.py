"""Bounded official YouTube streamList/gRPC worker."""
from __future__ import annotations
import math, threading, time
from dataclasses import dataclass
from typing import Any, Callable, Iterator
from .consent_registry import ConsentRegistry
from .polling_checkpoint_store import PollingCheckpointStore

@dataclass(frozen=True)
class StreamListResult:
    responses_received: int
    reconnects: int
    stopped_by_request: bool
    last_page_token: str | None
    offline: bool

class StreamListError(RuntimeError):
    """Sanitized non-retryable stream failure."""

def _status_name(error: BaseException) -> str | None:
    code = getattr(error, "code", None)
    if not callable(code): return None
    try: value = code()
    except Exception: return None
    name = getattr(value, "name", None)
    if isinstance(name, str): return name.upper()
    value_text = str(value).upper()
    return value_text.rsplit(".", 1)[-1] if value_text else None

def run_bounded_stream_list(*, registry: ConsentRegistry, video_id: str,
    live_chat_id: str, stream_factory: Callable[[str, str | None], Iterator[Any]],
    on_response: Callable[[Any], None], stop_event: threading.Event,
    max_responses: int, max_runtime_seconds: float, max_reconnects: int = 3,
    initial_backoff_seconds: float = 2.0, max_backoff_seconds: float = 30.0,
    wait: Callable[[float], bool] | None = None,
    monotonic: Callable[[], float] = time.monotonic,
    checkpoint_store: PollingCheckpointStore | None = None) -> StreamListResult:
    """Consume official server-streamed responses with bounded reconnect/resume.

    stream_factory(live_chat_id, page_token) creates the generated gRPC
    StreamList iterator. on_response must durably persist messages before
    returning. Delivery is at-least-once; callbacks must be idempotent.
    """
    if not isinstance(video_id, str) or not video_id.strip(): raise ValueError("video_id is required")
    if not isinstance(live_chat_id, str) or not live_chat_id.strip(): raise ValueError("live_chat_id is required")
    if not callable(stream_factory) or not callable(on_response): raise ValueError("callbacks are required")
    if not 1 <= max_responses <= 100000: raise ValueError("max_responses must be between 1 and 100000")
    if not 0 <= max_reconnects <= 100: raise ValueError("max_reconnects must be between 0 and 100")
    if not math.isfinite(max_runtime_seconds) or not 0 < max_runtime_seconds <= 86400:
        raise ValueError("max_runtime_seconds must be greater than 0 and at most 86400")
    if (not math.isfinite(initial_backoff_seconds) or initial_backoff_seconds <= 0
        or not math.isfinite(max_backoff_seconds) or max_backoff_seconds < initial_backoff_seconds):
        raise ValueError("backoff values must be finite, positive, and max >= initial")
    wait_fn = wait or stop_event.wait
    deadline = monotonic() + max_runtime_seconds
    checkpoint = checkpoint_store.load(video_id) if checkpoint_store else None
    if checkpoint and checkpoint.live_chat_id and checkpoint.live_chat_id != live_chat_id:
        raise ValueError("checkpoint live_chat_id does not match requested chat")
    page_token = checkpoint.page_token if checkpoint else None
    received = reconnects = 0
    offline = False
    while received < max_responses and not stop_event.is_set():
        if monotonic() >= deadline: break
        registry.require(video_id, "analyze_chat")
        try:
            stream = stream_factory(live_chat_id, page_token)
            for response in stream:
                if stop_event.is_set() or monotonic() >= deadline: break
                on_response(response)
                token = getattr(response, "next_page_token", None)
                offline_at = getattr(response, "offline_at", None)
                if checkpoint_store:
                    checkpoint_store.save(video_id, live_chat_id=live_chat_id, page_token=token or None)
                page_token = token or None
                received += 1
                if offline_at: offline = True; break
                if received >= max_responses: break
            if offline or received >= max_responses or stop_event.is_set(): break
            error_name = "UNAVAILABLE"
        except Exception as exc:
            error_name = _status_name(exc)
            if error_name not in {"UNAVAILABLE", "DEADLINE_EXCEEDED", "RESOURCE_EXHAUSTED"}:
                if error_name: raise StreamListError(f"YouTube stream failed: {error_name}") from None
                raise
        if reconnects >= max_reconnects: break
        reconnects += 1
        delay = min(initial_backoff_seconds * (2 ** (reconnects - 1)),
                    max_backoff_seconds, max(0.0, deadline - monotonic()))
        if delay <= 0 or wait_fn(delay): break
    return StreamListResult(received, reconnects, stop_event.is_set(), page_token, offline)
