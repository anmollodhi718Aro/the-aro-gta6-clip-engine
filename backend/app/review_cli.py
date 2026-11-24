"""CLI for recording a human review decision; no publishing path."""
from __future__ import annotations
import argparse,json,sys
from datetime import datetime,timezone
from pathlib import Path
from .review import ReviewLedger

def main():
    p=argparse.ArgumentParser(description="Record a local human review decision.")
    p.add_argument("clip_plan",type=Path); p.add_argument("--candidate-id",required=True)
    p.add_argument("--decision",required=True,choices=("approved","rejected"))
    p.add_argument("--reviewer",required=True,help="local label, not authenticated identity")
    p.add_argument("--ledger",type=Path,default=Path("review_ledger.json")); p.add_argument("--note",default="")
    a=p.parse_args()
    try:
        plan=json.loads(a.clip_plan.read_text(encoding="utf-8"))
        candidate=next((x for x in plan.get("candidates",[]) if x.get("candidate_id")==a.candidate_id),None)
        if candidate is None: raise ValueError("candidate is not in the supplied clip plan")
        if candidate.get("status")!="needs_review": raise ValueError("candidate is not awaiting review")
        ReviewLedger(a.ledger).record(a.candidate_id,str(candidate["source_id"]),a.decision,
            a.reviewer,datetime.now(timezone.utc),a.note)
    except (OSError,json.JSONDecodeError,KeyError,TypeError,ValueError) as exc:
        print(f"Review stopped: {exc}",file=sys.stderr); return 2
    print("Review decision recorded. This does not authorize upload or publication."); return 0

if __name__=="__main__": raise SystemExit(main())
