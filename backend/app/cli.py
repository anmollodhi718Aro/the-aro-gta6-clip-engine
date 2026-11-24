"""CLI for analyzing authorized chat events from JSON files."""
from __future__ import annotations
import argparse,json,sys
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from .detection import DetectorConfig,detect_chat_spikes
from .ingestion import normalize_event_batch
from .models import PermissionRecord
from .registry import SourceRegistry

def analyze_file(input_path:Path,output_path:Path,config:DetectorConfig,
                 registry_path:Path|None=None,source_id:str|None=None)->int:
    try:
        payload:dict[str,Any]=json.loads(input_path.read_text(encoding="utf-8"))
        if (registry_path is None)!=(source_id is None): raise ValueError("--registry and --source-id must be supplied together")
        if registry_path is not None and source_id is not None:
            source=SourceRegistry(registry_path).require(source_id,"analyze_chat",datetime.now(timezone.utc))
            permission=source.permission
        else: permission=PermissionRecord.from_dict(payload["permission"])
        events=normalize_event_batch(payload.get("events",[]),permission)
        candidates=detect_chat_spikes(events,permission,config)
        result={"source_id":permission.source_id,"candidate_count":len(candidates),
          "candidates":[x.to_dict() for x in candidates],"publishing_enabled":False}
        output_path.write_text(json.dumps(result,indent=2),encoding="utf-8")
        print(f"Wrote {len(candidates)} candidate(s) to {output_path}"); return 0
    except (OSError,json.JSONDecodeError,KeyError,TypeError,ValueError,PermissionError) as exc:
        print(f"Analysis stopped: {exc}",file=sys.stderr); return 2

def main():
    p=argparse.ArgumentParser(description="Analyze authorized chat events for highlight candidates.")
    p.add_argument("input",type=Path); p.add_argument("--output",type=Path,default=Path("clip_plan.json"))
    p.add_argument("--registry",type=Path); p.add_argument("--source-id")
    p.add_argument("--window-seconds",type=int,default=10); p.add_argument("--baseline-windows",type=int,default=3)
    p.add_argument("--spike-multiplier",type=float,default=2.0); p.add_argument("--min-messages",type=int,default=5)
    a=p.parse_args()
    if (a.registry is None)!=(a.source_id is None): p.error("--registry and --source-id must be supplied together")
    try: cfg=DetectorConfig(a.window_seconds,a.baseline_windows,a.spike_multiplier,a.min_messages)
    except ValueError as exc: p.error(str(exc))
    return analyze_file(a.input,a.output,cfg,a.registry,a.source_id)

if __name__=="__main__": raise SystemExit(main())
