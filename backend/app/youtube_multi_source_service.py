"""Optional bounded lifecycle manager for multiple authorized chat streams.

This module is inert until start_source is called. Each worker rechecks
consent before connecting and uses the existing durable checkpoint semantics.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Callable

from .consent_registry import ConsentRegistry
from .polling_checkpoint_store import PollingCheckpointStore
from .youtube_stream_list_worker import StreamListResult, run_bounded_stream_list


@dataclass(frozen=True)
class StreamSourceStatus:
    video_id: str
    state: str
    started: bool
    finished: bool
    error: str | None
    result: StreamListResult | None


@dataclass
class _ManagedSource:
    video_id: str
    stop_event: threading.Event
    thread: threading.Thread | None = None
    started: bool = False
    finished: bool = False
    error: str | None = None
    result: StreamListResult | None = None


class MultiSourceStreamService:
    """Manage a fixed upper bound of independently stoppable stream workers."""

    def __init__(
        self,
        *,
        registry: ConsentRegistry,
        max_concurrent_sources: int = 2,
        checkpoint_store: PollingCheckpointStore | None = None,
    ) -> None:
        if not isinstance(max_concurrent_sources, int) or not 1 <= max_concurrent_sources <= 32:
            raise ValueError("max_concurrent_sources must be between 1 and 32")
        if not isinstance(registry, ConsentRegistry):
            raise TypeError("registry must be a ConsentRegistry")
        self.registry = registry
        self.max_concurrent_sources = max_concurrent_sources
        self.checkpoint_store = checkpoint_store
        self._lock = threading.RLock()
        self._sources: dict[str, _ManagedSource] = {}

    def start_source(
        self,
        *,
        video_id: str,
        live_chat_id: str,
        stream_factory: Callable[[str, str | None], Any],
        on_response: Callable[[Any], None],
        max_responses: int,
        max_runtime_seconds: float,
        max_reconnects: int = 3,
        initial_backoff_seconds: float = 2.0,
        max_backoff_seconds: float = 30.0,
    ) -> StreamSourceStatus:
        if not isinstance(video_id, str) or not video_id.strip():
            raise ValueError("video_id is required")
        if not isinstance(live_chat_id, str) or not live_chat_id.strip():
            raise ValueError("live_chat_id is required")
        if not callable(stream_factory) or not callable(on_response):
            raise ValueError("stream_factory and on_response must be callable")
        with self._lock:
            existing = self._sources.get(video_id)
            if existing is not None and not existing.finished:
                raise ValueError("source is already running")
            active = sum(not item.finished for item in self._sources.values())
            if active >= self.max_concurrent_sources:
                raise RuntimeError("maximum concurrent source limit reached")

            managed = _ManagedSource(video_id=video_id, stop_event=threading.Event())
            managed.thread = threading.Thread(
                target=self._run_source,
                name=f"aro-stream-{video_id}",
                daemon=False,
                kwargs={
                    "managed": managed,
                    "live_chat_id": live_chat_id,
                    "stream_factory": stream_factory,
                    "on_response": on_response,
                    "max_responses": max_responses,
                    "max_runtime_seconds": max_runtime_seconds,
                    "max_reconnects": max_reconnects,
                    "initial_backoff_seconds": initial_backoff_seconds,
                    "max_backoff_seconds": max_backoff_seconds,
                },
            )
            self._sources[video_id] = managed
            try:
                managed.thread.start()
                managed.started = True
            except Exception:
                self._sources.pop(video_id, None)
                raise
            return self._snapshot(managed)

    def _run_source(
        self,
        *,
        managed: _ManagedSource,
        live_chat_id: str,
        stream_factory: Callable[[str, str | None], Any],
        on_response: Callable[[Any], None],
        max_responses: int,
        max_runtime_seconds: float,
        max_reconnects: int,
        initial_backoff_seconds: float,
        max_backoff_seconds: float,
    ) -> None:
        try:
            managed.result = run_bounded_stream_list(
                registry=self.registry,
                video_id=managed.video_id,
                live_chat_id=live_chat_id,
                stream_factory=stream_factory,
                on_response=on_response,
                stop_event=managed.stop_event,
                max_responses=max_responses,
                max_runtime_seconds=max_runtime_seconds,
                max_reconnects=max_reconnects,
                initial_backoff_seconds=initial_backoff_seconds,
                max_backoff_seconds=max_backoff_seconds,
                checkpoint_store=self.checkpoint_store,
            )
        except Exception as exc:
            managed.error = f"{type(exc).__name__}: {exc}"
        finally:
            with self._lock:
                managed.finished = True

    @staticmethod
    def _snapshot(managed: _ManagedSource) -> StreamSourceStatus:
        state = "failed" if managed.error else (
            "finished" if managed.finished else ("running" if managed.started else "starting")
        )
        return StreamSourceStatus(
            video_id=managed.video_id,
            state=state,
            started=managed.started,
            finished=managed.finished,
            error=managed.error,
            result=managed.result,
        )

    def status(self, video_id: str | None = None) -> tuple[StreamSourceStatus, ...]:
        with self._lock:
            if video_id is not None:
                item = self._sources.get(video_id)
                return () if item is None else (self._snapshot(item),)
            return tuple(self._snapshot(item) for item in self._sources.values())

    def stop_source(self, video_id: str, *, join_timeout: float = 5.0) -> bool:
        if not isinstance(video_id, str) or not video_id.strip():
            raise ValueError("video_id is required")
        if join_timeout < 0:
            raise ValueError("join_timeout must be non-negative")
        with self._lock:
            managed = self._sources.get(video_id)
            if managed is None or managed.finished:
                return False
            managed.stop_event.set()
            thread = managed.thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(join_timeout)
        return True

    def shutdown(self, *, join_timeout: float = 5.0) -> tuple[str, ...]:
        """Stop all workers and return IDs still active after bounded joins."""
        if join_timeout < 0:
            raise ValueError("join_timeout must be non-negative")
        with self._lock:
            active = [item for item in self._sources.values() if not item.finished]
            for item in active:
                item.stop_event.set()
        for item in active:
            if item.thread is not None and item.thread is not threading.current_thread():
                item.thread.join(join_timeout)
        with self._lock:
            return tuple(item.video_id for item in self._sources.values() if not item.finished)
