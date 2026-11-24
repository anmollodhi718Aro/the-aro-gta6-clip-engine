"""Append-only local review decisions; review never publishes media."""
from __future__ import annotations
import json, os, tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from .models import parse_datetime

@dataclass(frozen=True)
class ReviewDecision:
    candidate_id:str
    source_id:str
    decision:str
    reviewer_id:str
    decided_at:datetime
    note:str=""
    def __post_init__(self):
        if not self.candidate_id.strip() or not self.source_id.strip(): raise ValueError("candidate/source required")
        if self.decision not in {"approved","rejected"}: raise ValueError("decision must be approved or rejected")
        if not self.reviewer_id.strip(): raise ValueError("reviewer_id required")
        if len(self.note)>1000: raise ValueError("note exceeds 1000 characters")
        object.__setattr__(self,"decided_at",parse_datetime(self.decided_at))
    def to_dict(self):
        return {"candidate_id":self.candidate_id,"source_id":self.source_id,"decision":self.decision,
                "reviewer_id":self.reviewer_id,"decided_at":self.decided_at.isoformat(),"note":self.note}

class ReviewLedger:
    SCHEMA_VERSION=1
    def __init__(self,path:Path): self.path=Path(path).expanduser()
    def _read(self):
        if self.path.is_symlink(): raise ValueError("ledger path must not be a symbolic link")
        if not self.path.exists(): return {}
        try: data=json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc: raise ValueError("invalid review ledger JSON") from exc
        if not isinstance(data,dict) or data.get("schema_version")!=self.SCHEMA_VERSION:
            raise ValueError("unsupported review ledger schema")
        items=data.get("decisions")
        if not isinstance(items,list): raise ValueError("decisions must be a list")
        result={}
        for d in items:
            decision=ReviewDecision(str(d["candidate_id"]),str(d["source_id"]),str(d["decision"]),
                str(d["reviewer_id"]),parse_datetime(d["decided_at"]),str(d.get("note","")))
            if decision.candidate_id in result: raise ValueError("duplicate candidate decision")
            result[decision.candidate_id]=decision
        return result
    def _write(self,items):
        if self.path.is_symlink(): raise ValueError("ledger path must not be a symbolic link")
        self.path.parent.mkdir(parents=True,exist_ok=True)
        data={"schema_version":self.SCHEMA_VERSION,"decisions":[items[k].to_dict() for k in sorted(items)]}
        f=tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",newline="\n",
            prefix=f".{self.path.name}.",suffix=".tmp",dir=self.path.parent,delete=False)
        tmp=Path(f.name)
        try:
            with f:
                json.dump(data,f,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
            os.replace(tmp,self.path)
        finally: tmp.unlink(missing_ok=True)
    def get(self,candidate_id): return self._read().get(candidate_id)
    def record(self,candidate_id,source_id,decision,reviewer_id,decided_at,note=""):
        items=self._read()
        if candidate_id in items: raise ValueError("candidate already has a final decision")
        result=ReviewDecision(candidate_id,source_id,decision,reviewer_id,decided_at,note)
        items[candidate_id]=result; self._write(items); return result
