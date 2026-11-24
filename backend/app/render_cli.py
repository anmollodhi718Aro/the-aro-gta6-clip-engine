"""CLI for authorized local review-only rendering."""
from __future__ import annotations
import argparse,sys
from datetime import datetime,timezone
from pathlib import Path
from .registry import SourceRegistry
from .render import RenderError,render_clip

def main():
    p=argparse.ArgumentParser(description="Render local media with registered edit_media permission.")
    p.add_argument("input",type=Path); p.add_argument("output",type=Path)
    p.add_argument("--start",type=float,required=True); p.add_argument("--duration",type=float,required=True)
    p.add_argument("--registry",type=Path,required=True); p.add_argument("--source-id",required=True)
    p.add_argument("--confirm-rights",action="store_true")
    a=p.parse_args()
    try:
        source=SourceRegistry(a.registry).require(a.source_id,"edit_media",datetime.now(timezone.utc))
        result=render_clip(a.input,a.output,start_seconds=a.start,duration_seconds=a.duration,
                           rights_confirmed=a.confirm_rights,permission=source.permission)
    except (OSError,ValueError,PermissionError,RenderError) as exc:
        print(f"Render stopped: {exc}",file=sys.stderr); return 2
    print(f"Created review-only clip: {result}")
    print("Publishing is not available in this command."); return 0

if __name__=="__main__": raise SystemExit(main())
