"""Offline, escaped HTML dashboard for an evidence-backed creator ranking report."""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from .creator_watchlist_cli import _atomic_write_text


def _safe_source_link(value: object) -> str:
    if not isinstance(value, str):
        return ""
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        return ""
    return value


def load_ranking_report(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("ranking report must be a JSON object")
    rows = payload.get("rankings")
    if not isinstance(rows, list):
        raise ValueError("ranking report must contain a rankings array")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"rankings[{index}] must be an object")
        for field in ("rank", "creator", "views_7d", "live_streams_7d"):
            if field not in row:
                raise ValueError(f"rankings[{index}] is missing {field}")
        for field in ("views_7d", "live_streams_7d", "peak_concurrent_viewers"):
            if field in row and (isinstance(row[field], bool) or not isinstance(row[field], (int, float)) or row[field] < 0):
                raise ValueError(f"rankings[{index}].{field} must be a non-negative number")
    return payload


def render_dashboard(report: dict[str, object]) -> str:
    rows = report["rankings"]
    assert isinstance(rows, list)
    body_rows: list[str] = []
    for row in rows:
        assert isinstance(row, dict)
        creator = html.escape(str(row["creator"]))
        rank = html.escape(str(row["rank"]))
        views = html.escape(f"{row['views_7d']:,}")
        streams = html.escape(str(row["live_streams_7d"]))
        peak = html.escape(str(row.get("peak_concurrent_viewers", "N/A")))
        region = html.escape(str(row.get("region", "Unknown")))
        source = _safe_source_link(row.get("source_url"))
        source_cell = (
            f'<a href="{html.escape(source, quote=True)}" rel="noopener noreferrer">Evidence</a>'
            if source else "Not supplied"
        )
        body_rows.append(
            "<tr>"
            f"<td>{rank}</td><td>{creator}</td><td>{region}</td>"
            f"<td>{views}</td><td>{streams}</td><td>{peak}</td><td>{source_cell}</td>"
            "</tr>"
        )
    empty = '<tr><td colspan="7">No evidence-backed creator metrics supplied.</td></tr>'
    rows_html = "".join(body_rows) if body_rows else empty
    count = len(rows)
    period = html.escape(str(report.get("period_days", 7)))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>THE ARO | Creator Watchlist</title>
<style>
:root{{color-scheme:dark}}body{{font:16px system-ui,sans-serif;margin:0;background:#10131b;color:#edf1fa}}
main{{max-width:1100px;margin:40px auto;padding:0 20px}}h1{{margin-bottom:6px}}
.note{{color:#b9c4d8;line-height:1.5}}.stats{{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}}
.stat{{background:#1c2331;border:1px solid #344158;border-radius:12px;padding:14px 18px}}
table{{width:100%;border-collapse:collapse;background:#171d29;border-radius:12px;overflow:hidden}}
th,td{{text-align:left;padding:12px;border-bottom:1px solid #30394a}}th{{color:#b9c4d8}}
a{{color:#91c7ff}}footer{{margin-top:24px;color:#9eabc1;font-size:13px}}
@media(max-width:700px){{main{{margin:20px auto}}table{{font-size:13px}}th,td{{padding:8px}}}}
</style>
</head>
<body><main>
<h1>THE ARO Creator Watchlist</h1>
<p class="note">Evidence-backed activity snapshot. This is not a live ranking, future-view prediction, or permission to reuse creator content.</p>
<section class="stats">
<div class="stat"><strong>{count}</strong><br>ranked creators</div>
<div class="stat"><strong>{period} days</strong><br>measurement window</div>
<div class="stat"><strong>OFF</strong><br>publishing</div>
<div class="stat"><strong>OFF</strong><br>media downloads</div>
</section>
<table><thead><tr><th>Rank</th><th>Creator</th><th>Region</th><th>Views</th><th>Live streams</th><th>Peak viewers</th><th>Evidence</th></tr></thead>
<tbody>{rows_html}</tbody></table>
<footer>Generated locally. Missing metrics are not invented. Verify creator identity and source data before relying on this report.</footer>
</main></body></html>
"""


def run(input_path: Path, output_path: Path) -> int:
    try:
        report = load_ranking_report(input_path)
        _atomic_write_text(output_path, render_dashboard(report))
        print(f"Wrote offline creator dashboard to {output_path}")
        return 0
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"Creator dashboard stopped: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an offline HTML dashboard from a creator ranking JSON report.")
    parser.add_argument("input", type=Path, help="Creator ranking JSON report")
    parser.add_argument("--output", type=Path, default=Path("creator_watchlist.html"))
    args = parser.parse_args()
    return run(args.input, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
