"""Durable local source registry. Never store platform credentials here."""
from __future__ import annotations
import json, os, tempfile
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any
from .models import PermissionRecord, parse_datetime

@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    creator_name: str
    permission_evidence_ref: str
    permission: PermissionRecord
    owner_contact: str = ""
    permitted_platforms: tuple[str, ...] = ()
    attribution: str = ""
    def __post_init__(self):
        if not self.source_id.strip() or not self.creator_name.strip():
            raise ValueError("source_id and creator_name are required")
        if not self.permission_evidence_ref.strip():
            raise ValueError("permission_evidence_ref is required")
        if self.permission.source_id != self.source_id:
            raise ValueError("source and permission IDs must match")
    def to_dict(self):
        p=self.permission
        return {"source_id":self.source_id,"creator_name":self.creator_name,
          "owner_contact":self.owner_contact,"permission_evidence_ref":self.permission_evidence_ref,
          "permitted_platforms":list(self.permitted_platforms),"attribution":self.attribution,
          "permission":{"source_id":p.source_id,"granted_by":p.granted_by,"scopes":sorted(p.scopes),
            "granted_at":p.granted_at.isoformat(),
            "expires_at":p.expires_at.isoformat() if p.expires_at else None,
            "revoked_at":p.revoked_at.isoformat() if p.revoked_at else None}}
    @classmethod
    def from_dict(cls,d:dict[str,Any]):
        return cls(str(d["source_id"]),str(d["creator_name"]),str(d["permission_evidence_ref"]),
          PermissionRecord.from_dict(d["permission"]),str(d.get("owner_contact","")),
          tuple(str(x) for x in d.get("permitted_platforms",[])),str(d.get("attribution","")))

class SourceRegistry:
    """Atomic JSON registry for one local writer."""
    SCHEMA_VERSION=1
    def __init__(self,path:Path): self.path=Path(path).expanduser()
    def _read(self):
        if self.path.is_symlink(): raise ValueError("registry path must not be a symbolic link")
        if not self.path.exists(): return {}
        try: data=json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc: raise ValueError("invalid source registry JSON") from exc
        if not isinstance(data,dict) or data.get("schema_version")!=self.SCHEMA_VERSION:
            raise ValueError("unsupported source registry schema")
        items=data.get("sources")
        if not isinstance(items,list): raise ValueError("sources must be a list")
        result={}
        for item in items:
            record=SourceRecord.from_dict(item)
            if record.source_id in result: raise ValueError("duplicate source_id")
            result[record.source_id]=record
        return result
    def _write(self,records):
        if self.path.is_symlink(): raise ValueError("registry path must not be a symbolic link")
        self.path.parent.mkdir(parents=True,exist_ok=True)
        data={"schema_version":self.SCHEMA_VERSION,
              "sources":[records[k].to_dict() for k in sorted(records)]}
        f=tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",newline="\n",
          prefix=f".{self.path.name}.",suffix=".tmp",dir=self.path.parent,delete=False)
        tmp=Path(f.name)
        try:
            with f:
                json.dump(data,f,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
            os.replace(tmp,self.path)
        finally: tmp.unlink(missing_ok=True)
    def get(self,source_id): return self._read().get(source_id)
    def list_sources(self):
        d=self._read(); return [d[k] for k in sorted(d)]
    def register(self,record):
        d=self._read()
        if record.source_id in d: raise ValueError("source already registered")
        d[record.source_id]=record; self._write(d); return record
    def revoke(self,source_id,revoked_at:datetime):
        d=self._read()
        if source_id not in d: raise KeyError(source_id)
        old=d[source_id]
        if old.permission.revoked_at is not None: raise ValueError("permission already revoked")
        at=parse_datetime(revoked_at)
        if at<old.permission.granted_at: raise ValueError("revocation predates grant")
        updated=replace(old,permission=replace(old.permission,revoked_at=at))
        d[source_id]=updated; self._write(d); return updated
    def require(self,source_id,scope,at):
        record=self.get(source_id)
        if record is None or not record.permission.allows(scope,at):
            raise PermissionError(f"source {source_id!r} lacks active {scope!r} permission")
        return record
