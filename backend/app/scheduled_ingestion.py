"""One-request orchestration joining quota scheduling to safe chat ingestion."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .chat_event_store import ChatEventStore, IngestionResult
from .consent_registry import ConsentRegistry
from .polling_checkpoint_store import PollingCheckpointStore
from .quota_scheduler import QuotaAwareScheduler, ScheduledPoll
from .youtube_live_chat import YouTubeChatBatch, YouTubeLiveChatClient


@dataclass(frozen=True)
class ScheduledIngestion:
    reservation: ScheduledPoll
    batch: YouTubeChatBatch
    ingestion: IngestionResult


def poll_one_due_source(*, scheduler: QuotaAwareScheduler,
                        registry: ConsentRegistry,
                        client: YouTubeLiveChatClient,
                        checkpoints: PollingCheckpointStore,
                        events: ChatEventStore,
                        daily_quota_units: int,
                        now: datetime | None = None) -> ScheduledIngestion | None:
    """Reserve budget, re-check consent, fetch one page, persist, then checkpoint.

    This deliberately performs exactly one bounded API page request. Consent is
    revalidated after reservation and immediately before the API call. Failed
    requests keep their quota reservation conservatively; event persistence
    happens before cursor advancement so retries can be deduplicated.
    """
    reservation = scheduler.claim_next(daily_quota_units=daily_quota_units, now=now)
    if reservation is None:
        return None

    permission = registry.require(reservation.source_id, "analyze_chat")
    checkpoint = checkpoints.load(reservation.source_id)
    batch = client.fetch_recent_messages(
        reservation.source_id,
        permission,
        live_chat_id=checkpoint.live_chat_id if checkpoint else None,
        page_token=checkpoint.page_token if checkpoint else None,
    )
    ingestion = events.persist_batch(batch)
    checkpoints.save(
        reservation.source_id,
        live_chat_id=batch.live_chat_id,
        page_token=batch.next_page_token,
    )
    return ScheduledIngestion(reservation, batch, ingestion)
