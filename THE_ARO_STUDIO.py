#!/usr/bin/env python3
"""THE ARO Studio: single-file local dashboard and creator workflow.

Python 3.11+, standard library only. Binds to localhost by default.
It reads local render reports, creates original commentary packs from
operator-supplied research, and stores permission metadata locally.
It never downloads media, uploads, publishes, or verifies legal rights.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import secrets
import socket
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.parse import urlsplit
from typing import Any
from backend.app.rights_registry import SourceRightsRegistry
from backend.app.content_studio import build_content_pack, render_markdown as pack_markdown
from backend.app.content_preflight import preflight_content_pack
from backend.app.output_manager import write_json_no_overwrite, write_texts_no_overwrite
from backend.app.clock_sync import ClockAnchor, fit_clock_sync
from backend.app.creator_watchlist import SevenDayMetrics, ranking_report
from backend.app.creator_watchlist_dashboard import render_dashboard as render_creator_dashboard

APP_NAME = "THE ARO Studio"
STATUSES = {"planned", "rendered", "blocked", "not_approved", "failed"}
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def is_trusted_local_request(
    host_header: str,
    origin_header: str,
    fetch_site: str,
    expected_port: int,
) -> bool:
    """Reject DNS-rebinding and cross-site browser requests to the local server."""
    try:
        host = urlsplit("//" + host_header)
        if (
            host.hostname not in LOCAL_HOSTS
            or host.port != expected_port
            or host.username is not None
            or host.password is not None
            or host.path
            or host.query
            or host.fragment
        ):
            return False

        if origin_header:
            origin = urlsplit(origin_header)
            if (
                origin.scheme != "http"
                or origin.netloc.lower() != host.netloc.lower()
                or origin.path not in {"", "/"}
                or origin.query
                or origin.fragment
            ):
                return False

        if fetch_site and fetch_site.lower() not in {"same-origin", "none"}:
            return False
        return True
    except ValueError:
        return False


def is_valid_csrf_token(candidate: str, expected: str) -> bool:
    """Compare a form token without leaking timing information."""
    return bool(candidate and expected) and secrets.compare_digest(candidate, expected)


def server_class_for_host(host: str):
    """Select an address family matching the explicitly allowed loopback host."""
    if ":" in host:
        class IPv6ThreadingHTTPServer(ThreadingHTTPServer):
            address_family = socket.AF_INET6
        return IPv6ThreadingHTTPServer
    return ThreadingHTTPServer


def load_reports(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    if not root.exists():
        return rows, errors
    for path in sorted(root.rglob("*.json")):
        if path.name in {"content_pack.json"} or "rights" in path.parts:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                continue
            for index, item in enumerate(payload, 1):
                if not isinstance(item, dict) or item.get("status") not in STATUSES:
                    continue
                row = dict(item)
                row["candidate_row"] = row.get("candidate_row", index)
                row["report_file"] = str(path)
                rows.append(row)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
    return rows, errors


def build_clock_report(data: dict[str, Any]) -> dict[str, Any]:
    """Build a transparent clock calibration report from manually measured anchors."""
    if not isinstance(data, dict) or not isinstance(data.get("anchors"), list):
        raise ValueError("clock sync payload must contain an anchors array")
    anchors = []
    for index, item in enumerate(data["anchors"], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"clock anchor {index} must be an object")
        anchors.append(ClockAnchor(
            source_id=item.get("source_id"),
            chat_time=datetime.fromisoformat(str(item.get("chat_time", "")).replace("Z", "+00:00")),
            media_seconds=item.get("media_seconds"),
        ))
    sync = fit_clock_sync(
        anchors,
        max_residual_seconds=data.get("max_residual_seconds", 1.0),
        max_drift_ppm=data.get("max_drift_ppm", 1000.0),
    )
    return {
        "status": "calibrated",
        "source_id": sync.source_id,
        "anchor_count": len(anchors),
        "origin_chat_time": sync.origin_chat_time.isoformat(),
        "end_chat_time": sync.end_chat_time.isoformat(),
        "media_at_origin_seconds": sync.media_at_origin,
        "rate": sync.rate,
        "measured_max_residual_seconds": sync.max_residual_seconds,
        "max_residual_seconds": data.get("max_residual_seconds", 1.0),
        "max_drift_ppm": data.get("max_drift_ppm", 1000.0),
        "measured_drift_ppm": sync.drift_ppm,
        "anchors": [
            {
                "source_id": anchor.source_id,
                "chat_time": anchor.chat_time.isoformat(),
                "media_seconds": anchor.media_seconds,
            }
            for anchor in anchors
        ],
        "extrapolation_allowed": False,
        "human_marker_verification_required": True,
    }


def build_creator_report(data: dict[str, Any]) -> dict[str, Any]:
    """Rank only supplied, evidence-backed seven-day metrics."""
    if not isinstance(data, dict) or not isinstance(data.get("metrics"), list):
        raise ValueError("creator watchlist payload must contain a metrics array")
    metrics = []
    for index, item in enumerate(data["metrics"], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"metrics[{index - 1}] must be an object")
        for key in ("views", "live_streams"):
            if type(item.get(key)) is not int or item[key] < 0:
                raise ValueError(f"metrics[{index - 1}].{key} must be a non-negative integer")
        peak = item.get("peak_concurrent_viewers", 0)
        if type(peak) is not int or peak < 0:
            raise ValueError(f"metrics[{index - 1}].peak_concurrent_viewers must be a non-negative integer")
        average = item.get("average_concurrent_viewers", 0.0)
        if (isinstance(average, bool) or not isinstance(average, (int, float))
                or not math.isfinite(average) or average < 0):
            raise ValueError(f"metrics[{index - 1}].average_concurrent_viewers must be a finite non-negative number")
        metrics.append(SevenDayMetrics(
            creator_id=str(item.get("creator_id", "")),
            window_start=datetime.fromisoformat(str(item.get("window_start", "")).replace("Z", "+00:00")),
            window_end=datetime.fromisoformat(str(item.get("window_end", "")).replace("Z", "+00:00")),
            views=item["views"],
            live_streams=item["live_streams"],
            peak_concurrent_viewers=peak,
            average_concurrent_viewers=float(average),
            source_url=str(item.get("source_url", "")),
            captured_at=(
                datetime.fromisoformat(str(item["captured_at"]).replace("Z", "+00:00"))
                if item.get("captured_at") else None
            ),
        ))
    return ranking_report(metrics)


class RightsStore:
    """Dashboard adapter for the shared, preflight-compatible rights registry."""

    def __init__(self, path: Path):
        self.path = path.expanduser()
        self.registry = SourceRightsRegistry(self.path)

    def add(self, record: dict[str, Any]) -> None:
        self.registry.register(record, actor="THE ARO Studio local dashboard")

    def count(self) -> int:
        db = sqlite3.connect(self.path)
        try:
            return int(db.execute("SELECT COUNT(*) FROM source_rights").fetchone()[0])
        finally:
            db.close()

    def legacy_count(self) -> int:
        """Count old dashboard-only rows without deleting or silently migrating them."""
        db = sqlite3.connect(self.path)
        try:
            exists = db.execute("SELECT 1 FROM sqlite_master WHERE type=? AND name=?", ("table", "rights")).fetchone()
            if not exists:
                return 0
            return int(db.execute("SELECT COUNT(*) FROM rights").fetchone()[0])
        finally:
            db.close()

    def close(self) -> None:
        # The shared registry uses short-lived connections for each operation.
        return None

def page(rows: list[dict[str, Any]], errors: list[str], rights_count: int, notice: str = "", csrf_token: str = "", legacy_rights_count: int = 0) -> str:
    counts = Counter(str(r.get("status")) for r in rows)
    stats = "".join(
        f'<article class="stat"><span>{html.escape(s.replace("_", " ").title())}</span><b>{counts[s]}</b></article>'
        for s in ("planned", "rendered", "failed", "blocked", "not_approved")
    )
    body = []
    for r in rows:
        vals = [r.get("candidate_row", ""), r.get("source_id", ""), r.get("start_seconds", ""),
                r.get("end_seconds", ""), r.get("status", ""), r.get("message", ""), r.get("output_path", "")]
        cells = "".join(f"<td>{html.escape(str(v))}</td>" for v in vals)
        body.append(f"<tr>{cells}</tr>")
    table = "".join(body) or '<tr><td colspan="7">No batch reports found. Rendered reports will appear here.</td></tr>'
    error_html = "".join(f"<li>{html.escape(e)}</li>" for e in errors)
    safe_notice = f'<p class="notice">{html.escape(notice)}</p>' if notice else ""
    csrf_field = f'<input type="hidden" name="csrf_token" value="{html.escape(csrf_token, quote=True)}">'
    legacy_notice = ''
    if legacy_rights_count:
        legacy_notice = '<p class="notice">' + str(legacy_rights_count) + ' old permission record(s) are preserved in the legacy table. They are not visible to rights preflight yet. Review and re-enter each current permission grant.</p>'
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{APP_NAME}</title>
<style>
:root{{color-scheme:dark;--bg:#0c1018;--panel:#171f2c;--line:#2b394c;--muted:#9baac0;--txt:#edf3fb}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--txt);font:14px/1.55 system-ui;padding:22px}}
main{{max-width:1250px;margin:auto}}h1{{margin:0;font-size:28px}}h2{{font-size:18px;margin:0 0 12px}}
.muted,.hint{{color:var(--muted)}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:20px 0}}
.stat,.panel{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px}}
.stat span{{display:block;color:var(--muted)}}.stat b{{font-size:26px}}.columns{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
label{{display:block;margin:10px 0 5px;color:var(--muted)}}input,textarea,select{{width:100%;background:#0d1420;color:var(--txt);border:1px solid var(--line);border-radius:8px;padding:10px}}
textarea{{min-height:210px;font:12px/1.5 ui-monospace,monospace}}button{{margin-top:12px;padding:10px 15px;border:0;border-radius:8px;background:#6d5dfc;color:white;font-weight:700}}
.tablewrap{{overflow:auto;margin-top:12px}}table{{border-collapse:collapse;width:100%;min-width:850px}}td,th{{padding:10px;border-bottom:1px solid var(--line);text-align:left}}th{{color:var(--muted)}}
.notice{{background:#23344a;padding:10px;border-radius:8px}}.foot{{margin-top:18px;color:var(--muted);font-size:12px}}
@media(max-width:760px){{.columns{{grid-template-columns:1fr}}body{{padding:12px}}}}
</style></head><body><main>
<h1>THE ARO Studio</h1><p class="muted">One local workspace for clip review, original content drafts, and source-rights records.</p>{safe_notice}{legacy_notice}
<section class="grid">{stats}<article class="stat"><span>Rights records</span><b>{rights_count}</b></article></section>
<section class="columns">
<div class="panel"><h2>Original content pack</h2><p class="hint">Paste your own research notes as JSON. Each factual beat needs a source URL and original commentary.</p>
<form method="post" action="/generate">{csrf_field}<label>Research JSON</label><textarea name="payload" required>{html.escape(json.dumps({"working_title":"GTA 6: Sample topic","topic":"sample topic","original_angle":"An original analysis angle","research_notes":[{"claim":"Research-backed claim to verify","source_url":"https://example.com/source","aro_commentary":"Your own explanation in your words."}],"visual_assets":[{"asset_id":"aro-original-chart","kind":"original"}]},ensure_ascii=False,indent=2))}</textarea>
<button type="submit">Generate local draft</button></form></div>
<div class="panel"><h2>Source permission record</h2><p class="hint">Metadata only. This does not authenticate permission or provide legal clearance.</p>
<form method="post" action="/rights">{csrf_field}
<label>Source ID</label><input name="source_id" required>
<label>Source URL</label><input name="source_url" type="url" required>
<label>Grantor / creator</label><input name="grantor" required>
<label>Permission evidence reference</label><input name="evidence_ref" required>
<label>Allowed uses (comma separated: analyze, edit, publish)</label><input name="allowed_uses" placeholder="analyze, edit" required>
<label>Platforms (comma separated)</label><input name="platforms" placeholder="youtube" required>
<label>Valid from (ISO timestamp with timezone)</label><input name="valid_from" placeholder="2026-11-19T00:00:00+00:00" required>
<label>Expiry (optional ISO timestamp)</label><input name="expires_at">
<label>Attribution / disclosure</label><input name="attribution">
<button type="submit">Save rights metadata</button></form></div>
<div class="panel"><h2>Rights-aware visual preflight</h2><p class="hint">Check declared assets against the shared permission registry before editing or publishing. A metadata match is not legal clearance or upload approval.</p>
<form method="post" action="/preflight">{csrf_field}
<label>Target platform</label><input name="platform" value="youtube" required>
<label>Structured content pack JSON</label><textarea name="payload" required>{html.escape(json.dumps({"working_title":"GTA 6: Sample topic","topic":"sample topic","original_angle":"Original analysis","research_notes":[{"claim":"Claim to verify","source_url":"https://example.com/source","aro_commentary":"Our original explanation."}],"visual_assets":[{"asset_id":"aro-original-chart","kind":"original"}]},ensure_ascii=False,indent=2))}</textarea>
<button type="submit">Run rights preflight</button></form></div>
<div class="panel"><h2>Measured clock calibration</h2><p class="hint">Provide at least three manually matched chat/video markers from the same source. This tool rejects poor fits and never extrapolates beyond the anchors.</p>
<form method="post" action="/clock-sync">{csrf_field}
<label>Clock anchors JSON</label><textarea name="payload" required>{html.escape(json.dumps({"anchors":[{"source_id":"synthetic-authorized-stream","chat_time":"2026-11-19T12:00:00+00:00","media_seconds":5},{"source_id":"synthetic-authorized-stream","chat_time":"2026-11-19T12:01:00+00:00","media_seconds":65},{"source_id":"synthetic-authorized-stream","chat_time":"2026-11-19T12:02:00+00:00","media_seconds":125}],"max_residual_seconds":1.0,"max_drift_ppm":1000.0},ensure_ascii=False,indent=2))}</textarea>
<button type="submit">Calibrate clock</button></form></div>
<div class="panel"><h2>Creator watchlist</h2><p class="hint">Enter observed seven-day metrics with HTTPS evidence URLs. No scraping or invented metrics.</p>
<form method="post" action="/creator-watchlist">{csrf_field}
<label>Creator metrics JSON</label><textarea name="payload" required>{html.escape(json.dumps({"metrics":[{"creator_id":"techno-gamerz","window_start":"2026-11-12T00:00:00+00:00","window_end":"2026-11-19T00:00:00+00:00","views":0,"live_streams":0,"peak_concurrent_viewers":0,"average_concurrent_viewers":0,"source_url":"https://example.com/evidence"}]},ensure_ascii=False,indent=2))}</textarea>
<button type="submit">Generate offline creator report</button></form></div></section>
<section class="panel" style="margin-top:14px"><h2>Clip review reports</h2><p class="hint">Read-only view of local JSON batch reports. A rendered clip is not approved for publishing.</p>
<div class="tablewrap"><table><thead><tr><th>Row</th><th>Source</th><th>Start</th><th>End</th><th>Status</th><th>Details</th><th>Output</th></tr></thead><tbody>{table}</tbody></table></div></section>
{f'<section class="panel" style="margin-top:14px"><h2>Report warnings</h2><ul>{error_html}</ul></section>' if error_html else ""}
<p class="foot">Localhost only • Standard library only • No media upload/download • No automatic publishing • Human review required</p>
</main></body></html>"""


def serve(args: argparse.Namespace) -> int:
    data_dir = args.data_dir.expanduser().resolve()
    reports_dir = args.reports_dir.expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "source_rights.sqlite3"
    csrf_token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *values: Any) -> None:
            print("[THE ARO Studio] " + (fmt % values))

        def trusted_local_request(self) -> bool:
            return is_trusted_local_request(
                self.headers.get("Host", ""),
                self.headers.get("Origin", ""),
                self.headers.get("Sec-Fetch-Site", ""),
                args.port,
            )

        def send_html(self, content: str, status: int = 200) -> None:
            payload = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            if not self.trusted_local_request():
                self.send_html("Forbidden: local same-origin access only", 403)
                return
            if urlparse(self.path).path != "/":
                self.send_html("Not found", 404)
                return
            rows, errors = load_reports(reports_dir)
            store = RightsStore(db_path)
            count = store.count()
            legacy_count = store.legacy_count()
            store.close()
            self.send_html(page(
                rows, errors, count, csrf_token=csrf_token,
                legacy_rights_count=legacy_count,
            ))

        def do_POST(self) -> None:
            if not self.trusted_local_request():
                self.send_html("Forbidden: local same-origin access only", 403)
                return
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type != "application/x-www-form-urlencoded":
                self.send_html("Expected form-encoded request", 415)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_html("Invalid Content-Length", 400)
                return
            if length <= 0:
                self.send_html("Empty request body", 400)
                return
            if length > 1_000_000:
                self.send_html("Request too large", 413)
                return
            body = self.rfile.read(length)
            if len(body) != length:
                self.send_html("Incomplete request body", 400)
                return
            try:
                decoded_body = body.decode("utf-8")
            except UnicodeDecodeError:
                self.send_html("Request body must be UTF-8", 400)
                return
            fields = parse_qs(decoded_body, keep_blank_values=True)
            csrf_values = fields.get("csrf_token", [])
            if len(csrf_values) != 1 or not is_valid_csrf_token(csrf_values[0], csrf_token):
                self.send_html("Forbidden: invalid form token", 403)
                return
            notice = ""
            try:
                if self.path == "/generate":
                    raw = fields.get("payload", [""])[0]
                    data = json.loads(raw)
                    if not isinstance(data, dict):
                        raise ValueError("Top-level JSON must be an object.")
                    pack = build_content_pack(data)
                    out_dir = data_dir / "content_packs"
                    out_dir.mkdir(parents=True, exist_ok=True)
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                    stem = "".join(c if c.isalnum() or c in "-_" else "_" for c in pack["working_title"]).strip("_")[:48] or "aro_draft"
                    suffix = secrets.token_hex(8)
                    md_path = out_dir / f"{stem}_{stamp}_{suffix}.md"
                    json_path = out_dir / f"{stem}_{stamp}_{suffix}.json"
                    write_texts_no_overwrite({
                        md_path: pack_markdown(pack),
                        json_path: json.dumps(pack, ensure_ascii=False, indent=2) + "\n",
                    })
                    notice = f"Draft created locally: {md_path.name} and {json_path.name}. Upload approval remains false."
                elif self.path == "/preflight":
                    raw = fields.get("payload", [""])[0]
                    platform = fields.get("platform", [""])[0].strip()
                    pack = json.loads(raw)
                    registry = SourceRightsRegistry(db_path)
                    report = preflight_content_pack(pack, registry, platform)
                    out_dir = data_dir / "preflight_reports"
                    out_dir.mkdir(parents=True, exist_ok=True)
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                    report_path = out_dir / f"preflight_{stamp}_{secrets.token_hex(8)}.json"
                    write_json_no_overwrite(report_path, report)
                    notice = (
                        f"Preflight {report['status']}: {len(report['assets'])} asset(s) checked. "
                        f"Report saved as {report_path.name}. Human review remains required."
                    )
                elif self.path == "/clock-sync":
                    raw = fields.get("payload", [""])[0]
                    data = json.loads(raw)
                    report = build_clock_report(data)
                    out_dir = data_dir / "clock_calibrations"
                    out_dir.mkdir(parents=True, exist_ok=True)
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                    report_path = out_dir / f"clock_sync_{stamp}_{secrets.token_hex(3)}.json"
                    write_json_atomic(report_path, report)
                    notice = f"Clock calibrated for {report['source_id']} using {report['anchor_count']} markers. Report: {report_path.name}. No extrapolation allowed."
                elif self.path == "/creator-watchlist":
                    raw = fields.get("payload", [""])[0]
                    data = json.loads(raw)
                    report = build_creator_report(data)
                    out_dir = data_dir / "creator_watchlists"
                    out_dir.mkdir(parents=True, exist_ok=True)
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                    suffix = secrets.token_hex(3)
                    json_path = out_dir / f"creator_ranking_{stamp}_{suffix}.json"
                    html_path = out_dir / f"creator_watchlist_{stamp}_{suffix}.html"
                    write_texts_no_overwrite({
                        json_path: json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        html_path: render_creator_dashboard(report),
                    })
                    notice = f"Creator report generated: {json_path.name} and {html_path.name}. Ranking is provisional and does not grant reuse rights."
                elif self.path == "/rights":
                    def val(key: str) -> str:
                        return fields.get(key, [""])[0].strip()
                    record = {
                        "source_id": val("source_id"), "source_url": val("source_url"),
                        "grantor": val("grantor"), "evidence_ref": val("evidence_ref"),
                        "allowed_uses": [x.strip().lower() for x in val("allowed_uses").split(",") if x.strip()],
                        "platforms": [x.strip().lower() for x in val("platforms").split(",") if x.strip()],
                        "valid_from": val("valid_from"), "expires_at": val("expires_at") or None,
                        "attribution": val("attribution"), "disclosure": val("disclosure")
                    }
                    store = RightsStore(db_path)
                    store.add(record)
                    store.close()
                    notice = "Permission metadata saved locally. It has not been independently verified."
                else:
                    self.send_html("Not found", 404)
                    return
            except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, sqlite3.Error) as exc:
                notice = f"Action stopped: {exc}"
            rows, errors = load_reports(reports_dir)
            store = RightsStore(db_path)
            count = store.count()
            legacy_count = store.legacy_count()
            store.close()
            self.send_html(page(
                rows, errors, count, notice, csrf_token, legacy_count,
            ))

    server = server_class_for_host(args.host)((args.host, args.port), Handler)
    print(f"{APP_NAME} running at http://{args.host}:{server.server_port}")
    print(f"Reports: {reports_dir}")
    print(f"Local data: {data_dir}")
    print("Press Ctrl+C to stop. No external network interface is exposed by default.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping THE ARO Studio.")
    finally:
        server.server_close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the all-in-one THE ARO local dashboard.")
    parser.add_argument("--host", default="127.0.0.1", help="Keep localhost unless you understand network exposure.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", type=Path, default=Path("aro_studio_data"))
    parser.add_argument("--reports-dir", type=Path, default=Path("rendered_clips"))
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("For safety, this dashboard only binds to localhost.")
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    return serve(args)


if __name__ == "__main__":
    raise SystemExit(main())
