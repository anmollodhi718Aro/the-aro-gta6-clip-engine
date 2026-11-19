"""Build a review-ready original commentary pack from operator research notes.

This module does not fetch third-party footage or invent research. Each factual
beat must be supplied with a source URL; visuals default to original graphics
or media the operator owns or is authorized to use.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def _required_text(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def build_content_pack(data: dict[str, Any]) -> dict[str, Any]:
    title = _required_text(data, "working_title")
    topic = _required_text(data, "topic")
    angle = _required_text(data, "original_angle")
    notes = data.get("research_notes")
    if not isinstance(notes, list) or not notes:
        raise ValueError("research_notes must contain at least one sourced fact")
    beats = []
    for index, note in enumerate(notes, start=1):
        if not isinstance(note, dict):
            raise ValueError(f"research note {index} must be an object")
        claim = str(note.get("claim", "")).strip()
        source = str(note.get("source_url", "")).strip()
        parsed = urlparse(source)
        if not claim or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"research note {index} needs a claim and http(s) source_url")
        commentary = str(note.get("aro_commentary", "")).strip()
        if not commentary:
            raise ValueError(f"research note {index} needs original aro_commentary")
        beats.append({
            "claim": claim, "source_url": source,
            "aro_commentary": commentary,
            "visual": str(note.get("visual", "")).strip()
                      or "Create an original text card, diagram, or use authorized footage.",
        })

    raw_assets = data.get("visual_assets")
    if not isinstance(raw_assets, list) or not raw_assets:
        raise ValueError("visual_assets must contain at least one explicit visual declaration")
    visual_assets = []
    seen_asset_ids: set[str] = set()
    for index, asset in enumerate(raw_assets, start=1):
        if not isinstance(asset, dict):
            raise ValueError(f"visual_assets[{index - 1}] must be an object")
        asset_id = str(asset.get("asset_id", "")).strip()
        kind = str(asset.get("kind", "")).strip().lower()
        if not asset_id or asset_id in seen_asset_ids:
            raise ValueError(f"visual_assets[{index - 1}] needs a unique non-empty asset_id")
        if kind not in {"original", "licensed", "creator_authorized"}:
            raise ValueError(f"visual_assets[{index - 1}] kind must be original, licensed, or creator_authorized")
        source_id = str(asset.get("source_id", "")).strip()
        if kind != "original" and not source_id:
            raise ValueError(f"visual_assets[{index - 1}] requires source_id for {kind} material")
        seen_asset_ids.add(asset_id)
        visual_assets.append({
            "asset_id": asset_id,
            "kind": kind,
            "source_id": source_id or None,
            "description": str(asset.get("description", "")).strip(),
        })

    hook = str(data.get("hook", "")).strip() or f"GTA 6 में {topic} पर एक बात है जिसे समझना ज़रूरी है।"
    audience = str(data.get("audience", "GTA fans")).strip()
    cta = str(data.get("call_to_action", "ऐसी ही original GTA 6 explainers के लिए THE ARO को subscribe करें।")).strip()
    voiceover = [hook]
    for beat in beats:
        voiceover.extend([beat["claim"], beat["aro_commentary"]])
    voiceover.append(cta)
    visuals = [
        {"beat": "hook", "direction": "Original title animation and a self-made GTA 6 topic card."}
    ]
    visuals.extend({"beat": f"research_{i}", "direction": beat["visual"]}
                   for i, beat in enumerate(beats, start=1))
    visuals.append({"beat": "outro", "direction": "THE ARO end card made from original channel graphics."})
    return {
        "working_title": title, "topic": topic, "original_angle": angle,
        "audience": audience, "format": "YouTube Short / vertical 9:16",
        "voiceover_script": voiceover, "research_beats": beats,
        "visual_assets": visual_assets,
        "visual_plan": visuals,
        "metadata": {
            "description": (
                f"{title}\n\nTHE ARO की original commentary और analysis. "
                "सभी factual points के स्रोत नीचे दिए गए हैं।"
            ),
            "source_links": [beat["source_url"] for beat in beats],
            "tags": ["GTA6", "GTA6Hindi", "THEARO", "GamingAnalysis"],
        },
        "review": {
            "research_sources_present": True,
            "original_commentary_present": True,
            "human_fact_check_required": True,
            "rights_review_required_for_each_visual": True,
            "human_edit_review_required": True,
            "approved_for_upload": False,
            "monetization_guaranteed": False,
        },
    }


def render_markdown(pack: dict[str, Any]) -> str:
    lines = [
        f"# {pack['working_title']}", "", f"**Topic:** {pack['topic']}",
        f"**Original angle:** {pack['original_angle']}",
        f"**Audience:** {pack['audience']}", f"**Format:** {pack['format']}", "",
        "## Voiceover draft", "",
    ]
    lines.extend(f"{i}. {line}" for i, line in enumerate(pack["voiceover_script"], start=1))
    lines.extend(["", "## Research and source checks", ""])
    for i, beat in enumerate(pack["research_beats"], start=1):
        lines.extend([f"### Beat {i}", f"- Claim to verify: {beat['claim']}",
                      f"- Source: {beat['source_url']}",
                      f"- THE ARO commentary: {beat['aro_commentary']}", ""])
    lines.extend(["## Declared visual assets and rights", ""])
    lines.extend(
        f"- **{asset['asset_id']}**: {asset['kind']}"
        + (f" (source_id: {asset['source_id']})" if asset.get("source_id") else "")
        + (f" — {asset['description']}" if asset.get("description") else "")
        for asset in pack["visual_assets"]
    )
    lines.extend(["", "## Visual plan", ""])
    lines.extend(f"- **{item['beat']}**: {item['direction']}" for item in pack["visual_plan"])
    lines.extend(["", "## Upload description", "", pack["metadata"]["description"], "",
                  "## Pre-upload gate", "",
                  "- [ ] Verify every factual statement against its source.",
                  "- [ ] Confirm rights for every visual and audio asset.",
                  "- [ ] Review embedded music and third-party material separately.",
                  "- [ ] Add required attribution and disclosures.",
                  "- [ ] Review the finished edit and audio manually.",
                  "- [ ] Confirm platform rules and audience suitability.",
                  "- [ ] Human owner approves upload. This tool never uploads automatically.",
                  "", "> This is a production draft, not a copyright clearance or monetization guarantee.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an original THE ARO commentary production pack.")
    parser.add_argument("input", type=Path, help="JSON with sourced research notes and original commentary")
    parser.add_argument("--output", type=Path, default=Path("content_pack.md"))
    parser.add_argument("--json-output", type=Path, help="Optional structured JSON output")
    args = parser.parse_args()
    try:
        data = json.loads(args.input.expanduser().read_text(encoding="utf-8"))
        pack = build_content_pack(data)
        output = args.output.expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_markdown(pack), encoding="utf-8")
        if args.json_output:
            json_path = args.json_output.expanduser()
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": "draft_created", "output": str(output),
                          "approved_for_upload": False, "source_count": len(pack["research_beats"])},
                         ensure_ascii=False, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Content pack not created: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
