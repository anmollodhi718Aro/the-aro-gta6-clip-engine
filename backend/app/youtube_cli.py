"""One-shot YouTube public live-chat analysis CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .detection import DetectorConfig, detect_chat_spikes
from .models import PermissionRecord
from .youtube_live_chat import YouTubeLiveChatClient


def run(
    video_id: str,
    permission_path: Path,
    output_path: Path,
    *,
    live_chat_id: str | None = None,
    page_token: str | None = None,
    max_results: int = 200,
) -> int:
    try:
        permission_data: dict[str, Any] = json.loads(permission_path.read_text(encoding="utf-8"))
        permission = PermissionRecord.from_dict(permission_data)
        client = YouTubeLiveChatClient()
        batch = client.fetch_recent_messages(
            video_id,
            permission,
            live_chat_id=live_chat_id,
            page_token=page_token,
            max_results=max_results,
        )
        candidates = detect_chat_spikes(list(batch.events), permission, DetectorConfig())
        output = {
            "source_video_id": batch.video_id,
            "live_chat_id": batch.live_chat_id,
            "event_count": len(batch.events),
            "candidate_count": len(candidates),
            "candidates": [candidate.to_dict() for candidate in candidates],
            "next_page_token": batch.next_page_token,
            "polling_interval_ms": batch.polling_interval_ms,
            "offline": batch.offline,
            "publishing_enabled": False,
            "note": "Chat timestamps are not video offsets. Synchronization is required before rendering from these candidates.",
        }
        output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"Fetched {len(batch.events)} chat event(s); wrote {len(candidates)} candidate(s) to {output_path}")
        if batch.next_page_token:
            print(f"Next page token saved in output. Honor polling_interval_ms before requesting another page.")
        return 0
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, PermissionError, RuntimeError) as exc:
        print(f"YouTube analysis stopped: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze one bounded page of an authorized public YouTube live chat.")
    parser.add_argument("video_id")
    parser.add_argument("--permission", type=Path, required=True, help="JSON permission record for this video source")
    parser.add_argument("--output", type=Path, default=Path("youtube_clip_plan.json"))
    parser.add_argument("--live-chat-id", help="Reuse the live chat ID returned by the previous run")
    parser.add_argument("--page-token", help="Continue from the next_page_token in a previous output")
    parser.add_argument("--max-results", type=int, default=200)
    args = parser.parse_args()
    return run(
        args.video_id,
        args.permission,
        args.output,
        live_chat_id=args.live_chat_id,
        page_token=args.page_token,
        max_results=args.max_results,
    )


if __name__ == "__main__":
    raise SystemExit(main())
