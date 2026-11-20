"""Generate a self-contained, read-only HTML review dashboard from a batch report."""
from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from .output_manager import write_texts_no_overwrite


_ALLOWED_STATUSES = {"planned", "rendered", "blocked", "not_approved", "failed"}


def load_report(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path).expanduser()
    with source.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("batch report must be a JSON list")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"report row {index} must be a JSON object")
        status = item.get("status")
        if status not in _ALLOWED_STATUSES:
            raise ValueError(f"report row {index} has an unknown status")
        row = dict(item)
        row["candidate_row"] = item.get("candidate_row", index)
        rows.append(row)
    return rows


def render_dashboard(rows: list[dict[str, Any]], title: str = "Clip Review Dashboard") -> str:
    counts = Counter(str(row["status"]) for row in rows)
    cards = "".join(
        f'<article class="stat"><span>{html.escape(status.replace("_", " ").title())}</span>'
        f'<strong>{counts.get(status, 0)}</strong></article>'
        for status in ("planned", "rendered", "failed", "blocked", "not_approved")
    )
    body_rows = []
    for row in rows:
        status = str(row["status"])
        source_id = html.escape(str(row.get("source_id") or ""))
        message = html.escape(str(row.get("message") or ""))
        output = html.escape(str(row.get("output_path") or ""))
        start = html.escape(str(row.get("start_seconds", "")))
        end = html.escape(str(row.get("end_seconds", "")))
        candidate = html.escape(str(row.get("candidate_row", "")))
        body_rows.append(
            f'<tr><td><input class="row-select" type="checkbox" aria-label="Select candidate {candidate}"></td>'
            f'<td>{candidate}</td><td>{source_id}</td><td>{start}</td><td>{end}</td>'
            f'<td><span class="status {status}">{html.escape(status.replace("_", " "))}</span></td>'
            f'<td>{message}</td><td class="path">{output}</td></tr>'
        )
    safe_title = html.escape(title)
    table = "".join(body_rows) or '<tr><td colspan="8">No candidates in this report.</td></tr>'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe_title}</title>
<style>
:root{{color-scheme:dark;--bg:#10131b;--panel:#191f2b;--muted:#9aa8bb;--line:#303b4c;--text:#edf2f8}}
*{{box-sizing:border-box}}body{{margin:0;padding:28px;background:var(--bg);color:var(--text);font:14px/1.5 system-ui,sans-serif}}
main{{max-width:1400px;margin:auto}}h1{{margin:0 0 6px;font-size:26px}}.sub{{color:var(--muted);margin-bottom:22px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin-bottom:22px}}
.stat{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}}
.stat span{{display:block;color:var(--muted);font-size:12px}}.stat strong{{font-size:26px}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden}}
.toolbar{{padding:14px;border-bottom:1px solid var(--line);display:flex;gap:12px;flex-wrap:wrap}}
input,select{{background:#0e121a;color:var(--text);border:1px solid var(--line);padding:9px 11px;border-radius:8px}}
input{{min-width:220px;flex:1}}.table-wrap{{overflow:auto}}table{{width:100%;border-collapse:collapse;min-width:900px}}
th,td{{text-align:left;padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{color:var(--muted);font-weight:600;background:#151a24}}td.path{{max-width:220px;overflow-wrap:anywhere;color:var(--muted)}}
.status{{display:inline-block;border-radius:20px;padding:3px 8px;background:#303b4c;text-transform:capitalize}}
.status.rendered{{background:#174b39}}.status.failed{{background:#632e35}}.status.blocked{{background:#5a4723}}
.status.planned{{background:#24446a}}.status.not_approved{{background:#343b48}}
.note{{color:var(--muted);font-size:12px;margin-top:14px}}
@media(max-width:600px){{body{{padding:16px}}h1{{font-size:22px}}}}
</style>
</head>
<body><main>
<h1>{safe_title}</h1><div class="sub">Read-only local report view. No media is uploaded or transmitted.</div>
<section class="stats">{cards}</section>
<section class="panel"><div class="toolbar">
<input id="search" type="search" placeholder="Filter by candidate, source, or message" aria-label="Filter candidates">
<select id="status" aria-label="Filter by status"><option value="">All statuses</option>
<option>planned</option><option>rendered</option><option>failed</option><option>blocked</option><option>not_approved</option></select>
<button id="export-review" type="button">Export selected review rows</button>
</div><div class="table-wrap"><table><thead><tr>
<th>Select</th><th>Row</th><th>Source</th><th>Start (s)</th><th>End (s)</th><th>Status</th><th>Details</th><th>Output</th>
</tr></thead><tbody id="rows">{table}</tbody></table></div></section>
<div class="note">Review rendered clips manually. A rendered status is not an approval to publish.</div>
</main>
<script>
const search=document.getElementById('search'),status=document.getElementById('status');
function filterRows(){{const q=search.value.toLowerCase(),s=status.value;
document.querySelectorAll('#rows tr').forEach(row=>{{const text=row.textContent.toLowerCase();
row.hidden=!!((q&&!text.includes(q))||(s&&!row.querySelector('.status')?.classList.contains(s)));}});}}
search.addEventListener('input',filterRows);status.addEventListener('change',filterRows);
document.getElementById('export-review').addEventListener('click',()=>{{
  const selected=[...document.querySelectorAll('#rows input.row-select:checked')].map(box=>{{
    const cells=box.closest('tr').cells;
    return {{candidate_row:cells[1].textContent.trim(),source_id:cells[2].textContent.trim(),
      start_seconds:cells[3].textContent.trim(),end_seconds:cells[4].textContent.trim(),
      render_status:cells[5].textContent.trim(),review_selected:true}};
  }});
  const payload={{schema_version:1,kind:'aro_clip_review_selection',publish_approved:false,
    selected_count:selected.length,candidates:selected}};
  const blob=new Blob([JSON.stringify(payload,null,2)],{{type:'application/json'}});
  const url=URL.createObjectURL(blob),link=document.createElement('a');
  link.href=url;link.download='aro_review_selection.json';link.click();URL.revokeObjectURL(url);
}});
</script></body></html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local, read-only HTML dashboard from a batch render JSON report.")
    parser.add_argument("report", type=Path, help="batch_render_report.json")
    parser.add_argument("--output", type=Path, default=Path("clip_review_dashboard.html"))
    parser.add_argument("--title", default="Clip Review Dashboard")
    args = parser.parse_args()
    try:
        rows = load_report(args.report)
        output = args.output.expanduser()
        write_texts_no_overwrite({output: render_dashboard(rows, args.title)})
        print(f"Dashboard created: {output} ({len(rows)} candidates)")
        return 0
    except FileExistsError:
        print(f"Dashboard generation stopped: output already exists: {args.output.expanduser()}", file=sys.stderr)
        return 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Dashboard generation stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
