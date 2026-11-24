"""Validated data models for permissions, chat events, and clip candidates."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any

def parse_datetime(value:str|datetime)->datetime:
    parsed=value if isinstance(value,datetime) else datetime.fromisoformat(value.replace("Z","+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None: raise ValueError("timestamps must include a timezone")
    return parsed

@dataclass(frozen=True)
class PermissionRecord:
    source_id:str
    granted_by:str
    scopes:frozenset[str]
    granted_at:datetime
    expires_at:datetime|None=None
    revoked_at:datetime|None=None
    def __post_init__(self):
        if not self.source_id.strip() or not self.granted_by.strip(): raise ValueError("source_id and granted_by are required")
        object.__setattr__(self,"granted_at",parse_datetime(self.granted_at))
        if self.expires_at is not None:
            object.__setattr__(self,"expires_at",parse_datetime(self.expires_at))
            if self.expires_at<=self.granted_at: raise ValueError("permission expiry must follow grant time")
        if self.revoked_at is not None:
            object.__setattr__(self,"revoked_at",parse_datetime(self.revoked_at))
            if self.revoked_at<self.granted_at: raise ValueError("revocation cannot predate grant")
    def allows(self,scope,at):
        at=parse_datetime(at)
        if scope not in self.scopes or at<self.granted_at: return False
        if self.expires_at is not None and at>=self.expires_at: return False
        if self.revoked_at is not None and at>=self.revoked_at: return False
        return True
    @classmethod
    def from_dict(cls,data:dict[str,Any]):
        return cls(str(data["source_id"]),str(data["granted_by"]),
          frozenset(str(x) for x in data.get("scopes",[])),parse_datetime(data["granted_at"]),
          parse_datetime(data["expires_at"]) if data.get("expires_at") else None,
          parse_datetime(data["revoked_at"]) if data.get("revoked_at") else None)

@dataclass(frozen=True)
class ChatEvent:
    event_id:str
    source_id:str
    timestamp:datetime
    text:str=""
    def __post_init__(self):
        if not self.event_id.strip() or not self.source_id.strip(): raise ValueError("event_id and source_id are required")
        object.__setattr__(self,"timestamp",parse_datetime(self.timestamp))
    @classmethod
    def from_dict(cls,data:dict[str,Any]):
        return cls(str(data["event_id"]),str(data["source_id"]),parse_datetime(data["timestamp"]),str(data.get("text","")))

@dataclass(frozen=True)
class CandidateMoment:
    source_id:str
    peak_window_start:datetime
    clip_start:datetime
    clip_end:datetime
    peak_message_count:int
    baseline_average:float
    score:int
    explanation:str
    @property
    def candidate_id(self):
        key=f"{self.source_id}|{self.peak_window_start.isoformat()}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    def to_dict(self):
        return {"candidate_id":self.candidate_id,"source_id":self.source_id,
          "peak_window_start":self.peak_window_start.isoformat(),"clip_start":self.clip_start.isoformat(),
          "clip_end":self.clip_end.isoformat(),"peak_message_count":self.peak_message_count,
          "baseline_average":round(self.baseline_average,2),"score":self.score,
          "explanation":self.explanation,"status":"needs_review"}
