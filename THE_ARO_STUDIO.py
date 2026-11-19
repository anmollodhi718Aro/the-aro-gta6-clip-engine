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
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.parse import urlsplit
from typing import Any

APP_NAME = "THE ARO Studio"
STATUSES = {"planned", "rendered", "blocked", "not_approved", "failed"}


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


def build_content_pack(data: dict[str, Any]) -> dict[str, Any]:
    def required(key: str) -> str:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")
        return value.strip()

    title, topic, angle = required("working_title"), required("topic"), required("original_angle")
    notes = data.get("research_notes")
    if not isinstance(notes, list) or not notes:
        raise ValueError("research_notes must contain at least one sourced fact")
    beats = []
    for index, note in enumerate(notes, 1):
        if not isinstance(note, dict):
            raise ValueError(f"research_notes[{index - 1}] must be an object")
        claim = str(note.get("claim", "")).strip()
        commentary = str(note.get("aro_commentary", "")).strip()
        source = str(note.get("source_url", "")).strip()
        parsed = urlsplit(source)
        if not claim or not commentary or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"research note {index} needs claim, original aro_commentary, and http(s) source_url")
        beats.append({
            "claim": claim, "aro_commentary": commentary, "source_url": source,
            "visual": str(note.get("visual") or "Create original graphics or use footage explicitly authorized for this use.")
        })
    hook = str(data.get("hook") or f"GTA 6 में {topic} पर एक बात समझना ज़रूरी है।").strip()
    cta = str(data.get("call_to_action") or "ऐसी ही original GTA 6 analysis के लिए THE ARO को subscribe करें।").strip()
    voiceover = [hook]
    for beat in beats:
        voiceover.extend([beat["claim"], beat["aro_commentary"]])
    voiceover.append(cta)
    return {
        "working_title": title, "topic": topic, "original_angle": angle,
        "audience": str(data.get("audience") or "GTA fans"),
        "format": "YouTube Short / vertical 9:16",
        "voiceover_script": voiceover,
        "research_beats": beats,
        "visual_plan": [{"beat": "hook", "direction": "Original THE ARO title card."}]
            + [{"beat": f"research_{i}", "direction": beat["visual"]} for i, beat in enumerate(beats, 1)]
            + [{"beat": "outro", "direction": "Original THE ARO end card."}],
        "metadata": {
            "description": f"{title}\n\nTHE ARO की original commentary और analysis.",
            "source_links": [beat["source_url"] for beat in beats],
            "tags": ["GTA6", "GTA6Hindi", "THEARO", "GamingAnalysis"]
        },
        "review": {
            "human_fact_check_required": True, "rights_review_required_for_each_visual": True,
            "human_edit_review_required": True, "approved_for_upload": False,
            "monetization_guaranteed": False
        }
    }


def pack_markdown(pack: dict[str, Any]) -> str:
    lines = [f"# {pack['working_title']}", "", f"**Topic:** {pack['topic']}",
             f"**Original angle:** {pack['original_angle']}", f"**Audience:** {pack['audience']}",
             "", "## Voiceover draft", ""]
    lines += [f"{i}. {line}" for i, line in enumerate(pack["voiceover_script"], 1)]
    lines += ["", "## Research checks", ""]
    for i, beat in enumerate(pack["research_beats"], 1):
        lines += [f"### Beat {i}", f"- Claim: {beat['claim']}", f"- Source: {beat['source_url']}",
                  f"- THE ARO commentary: {beat['aro_commentary']}", ""]
    lines += ["## Visual plan", ""]
    lines += [f"- **{item['beat']}**: {item['direction']}" for item in pack["visual_plan"]]
    lines += ["", "## Pre-upload review", "", "- [ ] Fact-check every claim.",
              "- [ ] Confirm rights for every visual and audio asset.",
              "- [ ] Add required attribution and disclosures.",
              "- [ ] Review the finished edit manually.",
              "- [ ] Human owner explicitly approves any upload.",
              "", "> Draft only. This tool does not grant rights, verify claims, upload, or publish."]
    return "\n".join(lines) + "\n"


class RightsStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS rights (
            source_id TEXT PRIMARY KEY, source_url TEXT NOT NULL, grantor TEXT NOT NULL,
            evidence_ref TEXT NOT NULL, allowed_uses TEXT NOT NULL, platforms TEXT NOT NULL,
            attribution TEXT NOT NULL, disclosure TEXT NOT NULL, valid_from TEXT NOT NULL,
            expires_at TEXT, revoked_at TEXT)""")
        self.db.commit()

    def add(self, record: dict[str, Any]) -> None:
        required = ("source_id", "source_url", "grantor", "evidence_ref", "allowed_uses", "platforms", "valid_from")
        if any(not record.get(key) for key in required):
            raise ValueError("Missing required rights metadata fields.")
        parsed = urlsplit(str(record["source_url"]))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("source_url must be http(s)")
        uses = sorted(set(record["allowed_uses"]))
        if not uses or not set(uses).issubset({"analyze", "edit", "publish"}):
            raise ValueError("allowed_uses may contain analyze, edit, publish only")
        platforms = sorted(set(str(x).strip().lower() for x in record["platforms"] if str(x).strip()))
        if not platforms:
            raise ValueError("At least one platform is required")
        for key in ("valid_from", "expires_at"):
            value = record.get(key)
            if value:
                parsed_time = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                if parsed_time.tzinfo is None:
                    raise ValueError(f"{key} must include a timezone")
        self.db.execute("""INSERT INTO rights VALUES (?,?,?,?,?,?,?,?,?,?,NULL)
            ON CONFLICT(source_id) DO UPDATE SET source_url=excluded.source_url,
            grantor=excluded.grantor,evidence_ref=excluded.evidence_ref,
            allowed_uses=excluded.allowed_uses,platforms=excluded.platforms,
            attribution=excluded.attribution,disclosure=excluded.disclosure,
            valid_from=excluded.valid_from,expires_at=excluded.expires_at,revoked_at=NULL""",
            (str(record["source_id"]).strip(), str(record["source_url"]).strip(),
             str(record["grantor"]).strip(), str(record["evidence_ref"]).strip(),
             json.dumps(uses), json.dumps(platforms), str(record.get("attribution", "")),
             str(record.get("disclosure", "")), str(record["valid_from"]),
             str(record.get("expires_at") or "") or None))
        self.db.commit()

    def count(self) -> int:
        return int(self.db.execute("SELECT COUNT(*) FROM rights").fetchone()[0])

    def close(self) -> None:
        self.db.close()


def page(rows: list[dict[str, Any]], errors: list[str], rights_count: int, notice: str = "") -> str:
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
<h1>THE ARO Studio</h1><p class="muted">One local workspace for clip review, original content drafts, and source-rights records.</p>{safe_notice}
<section class="grid">{stats}<article class="stat"><span>Rights records</span><b>{rights_count}</b></article></section>
<section class="columns">
<div class="panel"><h2>Original content pack</h2><p class="hint">Paste your own research notes as JSON. Each factual beat needs a source URL and original commentary.</p>
<form method="post" action="/generate"><label>Research JSON</label><textarea name="payload" required>{html.escape(json.dumps({"working_title":"GTA 6: Sample topic","topic":"sample topic","original_angle":"An original analysis angle","research_notes":[{"claim":"Research-backed claim to verify","source_url":"https://example.com/source","aro_commentary":"Your own explanation in your words."}]},ensure_ascii=False,indent=2))}</textarea>
<button type="submit">Generate local draft</button></form></div>
<div class="panel"><h2>Source permission record</h2><p class="hint">Metadata only. This does not authenticate permission or provide legal clearance.</p>
<form method="post" action="/rights">
<label>Source ID</label><input name="source_id" required>
<label>Source URL</label><input name="source_url" type="url" required>
<label>Grantor / creator</label><input name="grantor" required>
<label>Permission evidence reference</label><input name="evidence_ref" required>
<label>Allowed uses (comma separated: analyze, edit, publish)</label><input name="allowed_uses" placeholder="analyze, edit" required>
<label>Platforms (comma separated)</label><input name="platforms" placeholder="youtube" required>
<label>Valid from (ISO timestamp with timezone)</label><input name="valid_from" placeholder="2026-11-19T00:00:00+00:00" required>
<label>Expiry (optional ISO timestamp)</label><input name="expires_at">
<label>Attribution / disclosure</label><input name="attribution">
<button type="submit">Save rights metadata</button></form></div></section>
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

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *values: Any) -> None:
            print("[THE ARO Studio] " + (fmt % values))

        def send_html(self, content: str, status: int = 200) -> None:
            payload = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            if urlparse(self.path).path != "/":
                self.send_html("Not found", 404)
                return
            rows, errors = load_reports(reports_dir)
            store = RightsStore(db_path)
            count = store.count()
            store.close()
            self.send_html(page(rows, errors, count))

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1_000_000:
                self.send_html("Request too large", 413)
                return
            fields = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
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
                    md_path = out_dir / f"{stem}_{stamp}.md"
                    json_path = out_dir / f"{stem}_{stamp}.json"
                    md_path.write_text(pack_markdown(pack), encoding="utf-8")
                    json_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
                    notice = f"Draft created locally: {md_path.name} and {json_path.name}. Upload approval remains false."
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
            except (ValueError, TypeError, KeyError, json.JSONDecodeError, sqlite3.Error) as exc:
                notice = f"Action stopped: {exc}"
            rows, errors = load_reports(reports_dir)
            store = RightsStore(db_path)
            count = store.count()
            store.close()
            self.send_html(page(rows, errors, count, notice))

    server = ThreadingHTTPServer((args.host, args.port), Handler)
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
