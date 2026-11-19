"""Read-only adapter for public YouTube live chat via the official Data API.

This adapter uses the documented REST list methods as a bounded fallback.
For continuous low-latency ingestion, the official streamList/gRPC path should
be implemented in a later worker milestone.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import ChatEvent, PermissionRecord


API_BASE = "https://www.googleapis.com/youtube/v3"
DEFAULT_TIMEOUT_SECONDS = 15


class YouTubeApiError(RuntimeError):
    """Sanitized YouTube API failure; never includes the API key or request URL."""


@dataclass(frozen=True)
class YouTubeChatBatch:
    video_id: str
    live_chat_id: str
    events: tuple[ChatEvent, ...]
    next_page_token: str | None
    polling_interval_ms: int | None
    offline: bool


class YouTubeLiveChatClient:
    """Small stdlib-only client for public live chat; no OAuth or write methods."""

    def __init__(self, api_key: str | None = None, timeout: int = DEFAULT_TIMEOUT_SECONDS):
        self._api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self._api_key:
            raise ValueError("Set YOUTUBE_API_KEY in the environment before using the YouTube adapter")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self._timeout = timeout

    def _get(self, endpoint: str, params: dict[str, str | int]) -> dict[str, Any]:
        query = urlencode({**params, "key": self._api_key})
        request = Request(
            f"{API_BASE}/{endpoint}?{query}",
            headers={"Accept": "application/json", "User-Agent": "THE-ARO-GTA6-Clip-Engine/0.1"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            reason = "request rejected"
            try:
                body = json.loads(exc.read().decode("utf-8"))
                reason = str(body.get("error", {}).get("errors", [{}])[0].get("reason", reason))
            except (ValueError, AttributeError, IndexError, TypeError):
                pass
            raise YouTubeApiError(f"YouTube API returned HTTP {exc.code}: {reason}") from None
        except (URLError, TimeoutError, OSError):
            raise YouTubeApiError("Could not reach the YouTube API; check connection and retry later") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise YouTubeApiError("YouTube API returned an invalid JSON response") from None

        if not isinstance(payload, dict):
            raise YouTubeApiError("YouTube API returned an unexpected response")
        if "error" in payload:
            reason = str(payload["error"].get("message", "API request failed"))
            raise YouTubeApiError(f"YouTube API error: {reason}")
        return payload

    def get_active_live_chat_id(self, video_id: str) -> str:
        if not video_id.strip():
            raise ValueError("video_id is required")
        payload = self._get("videos", {"part": "liveStreamingDetails", "id": video_id})
        items = payload.get("items", [])
        if not items:
            raise YouTubeApiError("Video was not found or is not publicly accessible through this API key")
        chat_id = items[0].get("liveStreamingDetails", {}).get("activeLiveChatId")
        if not chat_id:
            raise YouTubeApiError("This video has no currently active public live chat")
        return str(chat_id)

    def fetch_recent_messages(
        self,
        video_id: str,
        permission: PermissionRecord,
        *,
        live_chat_id: str | None = None,
        page_token: str | None = None,
        max_results: int = 200,
    ) -> YouTubeChatBatch:
        """Fetch one bounded page; caller controls subsequent calls and quota."""
        if permission.source_id != video_id:
            raise ValueError("permission source_id must match the YouTube video ID")
        if not permission.allows("analyze_chat", datetime.now(timezone.utc)):
            raise PermissionError("valid analyze_chat permission is required before API access")
        if not 200 <= max_results <= 2000:
            raise ValueError("max_results must be between 200 and 2000")

        chat_id = live_chat_id or self.get_active_live_chat_id(video_id)
        params: dict[str, str | int] = {
            "part": "id,snippet",
            "liveChatId": chat_id,
            "maxResults": max_results,
        }
        if page_token:
            params["pageToken"] = page_token
        payload = self._get("liveChat/messages", params)

        events: list[ChatEvent] = []
        for item in payload.get("items", []):
            snippet = item.get("snippet", {})
            message_text = snippet.get("displayMessage") or snippet.get("textMessageDetails", {}).get("messageText", "")
            if not item.get("id") or not snippet.get("publishedAt") or not message_text:
                continue
            events.append(ChatEvent(
                event_id=str(item["id"]),
                source_id=video_id,
                timestamp=str(snippet["publishedAt"]),
                text=str(message_text),
            ))

        interval = payload.get("pollingIntervalMillis")
        return YouTubeChatBatch(
            video_id=video_id,
            live_chat_id=chat_id,
            events=tuple(events),
            next_page_token=payload.get("nextPageToken"),
            polling_interval_ms=int(interval) if interval is not None else None,
            offline=bool(payload.get("offlineAt")),
        )
