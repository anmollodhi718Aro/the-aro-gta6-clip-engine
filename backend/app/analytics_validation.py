"""Dependency-free structural validation for the canonical AI session ledger."""
from __future__ import annotations

from datetime import datetime
from math import isclose, isfinite
import re
from typing import Any

CHAT_ID = re.compile(r"^ARO-CHAT-[0-9]{4}$")
WEIGHT_KEYS = (
    "task_importance",
    "verified_completion",
    "technical_correctness",
    "test_and_ci_evidence",
    "time_efficiency",
    "documentation_and_handoff",
)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone offset")
    return parsed


def validate_analytics_ledger(payload: Any) -> None:
    """Raise ValueError for malformed records; return None for a valid ledger.

    This validator intentionally uses only the Python standard library. It
    validates the durable fields needed for identity, attribution, timing,
    evidence, and scoring without treating missing measurements as zero.
    """
    if not isinstance(payload, dict):
        raise ValueError("ledger must be a JSON object")
    if payload.get("schema_version") != "1.0.0":
        raise ValueError("schema_version must be '1.0.0'")

    scoring = payload.get("scoring_model")
    if not isinstance(scoring, dict):
        raise ValueError("scoring_model must be an object")
    weights = scoring.get("weights")
    if not isinstance(weights, dict) or set(weights) != set(WEIGHT_KEYS):
        raise ValueError("scoring_model.weights must contain exactly the six documented dimensions")
    for key in WEIGHT_KEYS:
        value = weights[key]
        if not _is_number(value) or not 0 <= value <= 1:
            raise ValueError(f"weight {key} must be a finite number between 0 and 1")
    if not isclose(sum(weights.values()), 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("scoring weights must sum to 1.0")

    sessions = payload.get("sessions")
    if not isinstance(sessions, list):
        raise ValueError("sessions must be an array")
    seen: set[str] = set()
    for index, session in enumerate(sessions):
        prefix = f"sessions[{index}]"
        if not isinstance(session, dict):
            raise ValueError(f"{prefix} must be an object")
        required_fields = {
            "chat_id", "title", "project", "workstream_id", "task_ids", "provider", "model",
            "started_at", "ended_at", "elapsed_seconds", "active_work_seconds", "commits",
            "pull_requests", "issues", "tests", "ci_status", "windows_status",
            "real_media_status", "score", "evidence",
        }
        missing = required_fields - set(session)
        if missing:
            separator = ", "
            raise ValueError(f"{prefix} is missing required fields: {separator.join(sorted(missing))}")
        chat_id = session.get("chat_id")
        if not isinstance(chat_id, str) or not CHAT_ID.fullmatch(chat_id):
            raise ValueError(f"{prefix}.chat_id must match ARO-CHAT-NNNN")
        if chat_id in seen:
            raise ValueError(f"duplicate chat_id: {chat_id}")
        seen.add(chat_id)

        for field in ("title", "project", "workstream_id", "provider", "model", "ci_status", "windows_status", "real_media_status"):
            if not isinstance(session.get(field), str) or not session[field].strip():
                raise ValueError(f"{prefix}.{field} must be a non-empty string")
        task_ids = session.get("task_ids")
        if not isinstance(task_ids, list) or any(not isinstance(item, str) or not item.strip() for item in task_ids):
            raise ValueError(f"{prefix}.task_ids must be an array of non-empty strings")

        started = _timestamp(session.get("started_at"), f"{prefix}.started_at")
        ended_value = session.get("ended_at")
        if ended_value is not None:
            ended = _timestamp(ended_value, f"{prefix}.ended_at")
            if ended < started:
                raise ValueError(f"{prefix}.ended_at must not precede started_at")

        for field in ("elapsed_seconds", "active_work_seconds"):
            value = session.get(field)
            if value is not None and (not _is_number(value) or value < 0):
                raise ValueError(f"{prefix}.{field} must be null or a finite non-negative number")

        for field in ("commits", "pull_requests", "issues"):
            values = session.get(field)
            if not isinstance(values, list):
                raise ValueError(f"{prefix}.{field} must be an array")
            if field == "commits":
                valid = all(isinstance(item, str) and len(item) >= 7 for item in values)
            else:
                valid = all(isinstance(item, int) and not isinstance(item, bool) and item > 0 for item in values)
            if not valid:
                raise ValueError(f"{prefix}.{field} contains an invalid identifier")

        if not isinstance(session.get("tests"), dict):
            raise ValueError(f"{prefix}.tests must be an object")
        if not isinstance(session.get("evidence"), dict):
            raise ValueError(f"{prefix}.evidence must be an object")
        score = session.get("score")
        if score is not None and (not _is_number(score) or not 0 <= score <= 100):
            raise ValueError(f"{prefix}.score must be null or a finite number between 0 and 100")
