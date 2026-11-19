"""Transparent seven-day GTA creator ranking; no scraping or media downloads."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable
from urllib.parse import urlparse

WINDOW = timedelta(days=7)


@dataclass(frozen=True)
class Creator:
    creator_id: str
    display_name: str
    region: str
    identity_needs_verification: bool = True


# Candidate watchlist only. This is not a verified live-status list or a fixed ranking.
DEFAULT_CREATORS: tuple[Creator, ...] = (
    Creator("mythpat", "Mythpat", "India"),
    Creator("tgg", "TGG", "Global"),
    Creator("gamerfleet", "GamerFleet", "India"),
    Creator("techno-gamerz", "Techno Gamerz", "India"),
    Creator("carryislive", "CarryisLive", "India"),
    Creator("total-gaming", "Total Gaming", "India"),
    Creator("gta-series-videos", "GTA Series Videos", "Global"),
    Creator("mrbossftw", "MrBossFTW", "Global"),
    Creator("typical-gamer", "Typical Gamer", "Global"),
    Creator("live-insaan", "Live Insaan", "India"),
    Creator("dynamo-gaming", "Dynamo Gaming", "India"),
    Creator("gyan-gaming", "Gyan Gaming", "India"),
    Creator("ishowspeed", "iShowSpeed", "Global"),
    Creator("pewdiepie", "PewDiePie", "Global"),
    Creator("death-rush-gaming", "Death Rush Gaming", "Unverified"),
    Creator("death-tracks-gaming", "Death Tracks Gaming", "Unverified"),
)


@dataclass(frozen=True)
class SevenDayMetrics:
    creator_id: str
    window_start: datetime
    window_end: datetime
    views: int
    live_streams: int
    peak_concurrent_viewers: int = 0
    average_concurrent_viewers: float = 0.0
    source_url: str = ""
    captured_at: datetime | None = None

    def validate(self) -> None:
        if not isinstance(self.creator_id, str) or not self.creator_id.strip():
            raise ValueError("creator_id is required")
        for name, value in (("window_start", self.window_start), ("window_end", self.window_end)):
            if not isinstance(value, datetime):
                raise ValueError(f"{name} must be a datetime")
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.window_end - self.window_start != WINDOW:
            raise ValueError("metrics must cover exactly seven days")
        for name, value in (
            ("views", self.views),
            ("live_streams", self.live_streams),
            ("peak_concurrent_viewers", self.peak_concurrent_viewers),
        ):
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        average = self.average_concurrent_viewers
        if (
            isinstance(average, bool)
            or not isinstance(average, (int, float))
            or not math.isfinite(average)
            or average < 0
        ):
            raise ValueError("average_concurrent_viewers must be a finite non-negative number")
        if self.captured_at is not None:
            if not isinstance(self.captured_at, datetime):
                raise ValueError("captured_at must be a datetime")
            if self.captured_at.tzinfo is None or self.captured_at.utcoffset() is None:
                raise ValueError("captured_at must be timezone-aware")
        if not isinstance(self.source_url, str):
            raise ValueError("source_url must be an HTTPS evidence URL")
        parsed = urlparse(self.source_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("source_url must be an HTTPS evidence URL")


def rank_seven_day_creators(
    metrics: Iterable[SevenDayMetrics],
    creators: Iterable[Creator] = DEFAULT_CREATORS,
) -> list[dict[str, object]]:
    """Rank creators by observed 7-day views; use live audience as tie-breakers.

    Only supplied, evidence-linked metric rows are ranked. Missing creators are
    omitted rather than assigned invented zeroes. This is an activity ranking,
    not a prediction of future views or permission to reuse anyone's content.
    """
    creator_map = {creator.creator_id: creator for creator in creators}
    seen: set[str] = set()
    validated: list[tuple[Creator, SevenDayMetrics]] = []

    for row in metrics:
        row.validate()
        if row.creator_id in seen:
            raise ValueError(f"duplicate metrics for creator: {row.creator_id}")
        seen.add(row.creator_id)
        creator = creator_map.get(row.creator_id)
        if creator is None:
            raise ValueError(f"unknown creator_id: {row.creator_id}")
        validated.append((creator, row))

    validated.sort(
        key=lambda pair: (
            -pair[1].views,
            -pair[1].peak_concurrent_viewers,
            -pair[1].average_concurrent_viewers,
            pair[0].creator_id,
        )
    )
    return [
        {
            "rank": index,
            "creator_id": creator.creator_id,
            "creator": creator.display_name,
            "region": creator.region,
            "views_7d": row.views,
            "live_streams_7d": row.live_streams,
            "peak_concurrent_viewers": row.peak_concurrent_viewers,
            "average_concurrent_viewers": row.average_concurrent_viewers,
            "window_start": row.window_start.isoformat(),
            "window_end": row.window_end.isoformat(),
            "source_url": row.source_url,
            "captured_at": row.captured_at.isoformat() if row.captured_at else None,
            "identity_needs_verification": creator.identity_needs_verification,
            "ranking_basis": "7-day views; live audience used only as tie-breakers",
        }
        for index, (creator, row) in enumerate(validated, start=1)
    ]


def ranking_report(metrics: Iterable[SevenDayMetrics]) -> dict[str, object]:
    rows = rank_seven_day_creators(metrics)
    return {
        "period_days": 7,
        "ranked_count": len(rows),
        "rankings": rows,
        "ranking_is_provisional": True,
        "publishing_enabled": False,
        "media_download_enabled": False,
    }
