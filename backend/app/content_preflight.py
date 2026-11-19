"""Rights-aware preflight for visual assets in an original content pack.

This is a fail-closed metadata check, not legal advice or verification of
permission evidence. It never fetches, downloads, edits, uploads, or publishes.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.rights_registry import SourceRightsRegistry
from backend.app.output_manager import write_json_atomic


def preflight_content_pack(
    pack: dict[str, Any],
    registry: SourceRightsRegistry,
    platform: str,
    *,
    at: datetime | None = None,
) -> dict[str, Any]:
    if not isinstance(pack, dict):
        raise ValueError("content pack must be an object")
    if not isinstance(platform, str) or not platform.strip():
        raise ValueError("platform must be a non-empty string")
    assets = pack.get("visual_assets", [])
    if not isinstance(assets, list):
        raise ValueError("visual_assets must be a list")

    checked: list[dict[str, Any]] = []
    errors: list[str] = []
    if not assets:
        errors.append("content pack must declare at least one visual asset")
    required_attributions: list[str] = []
    required_disclosures: list[str] = []
    seen_ids: set[str] = set()

    for index, asset in enumerate(assets):
        prefix = f"visual_assets[{index}]"
        if not isinstance(asset, dict):
            errors.append(f"{prefix} must be an object")
            continue
        asset_id = str(asset.get("asset_id", "")).strip()
        kind = str(asset.get("kind", "")).strip().lower()
        if not asset_id:
            errors.append(f"{prefix} needs a non-empty asset_id")
            continue
        if asset_id in seen_ids:
            errors.append(f"{prefix} duplicates asset_id {asset_id}")
            continue
        seen_ids.add(asset_id)

        if kind == "original":
            checked.append({
                "asset_id": asset_id,
                "kind": kind,
                "status": "declared_original_requires_human_confirmation",
            })
            continue
        if kind not in {"licensed", "creator_authorized"}:
            errors.append(f"{prefix} kind must be original, licensed, or creator_authorized")
            continue

        source_id = str(asset.get("source_id", "")).strip()
        if not source_id:
            errors.append(f"{prefix} requires source_id for {kind} material")
            continue
        try:
            edit_grant = registry.authorize(source_id, "edit", platform, at=at)
            publish_grant = registry.authorize(source_id, "publish", platform, at=at)
        except (PermissionError, ValueError) as exc:
            errors.append(f"{prefix} blocked: {exc}")
            checked.append({
                "asset_id": asset_id, "kind": kind, "source_id": source_id,
                "status": "blocked", "reason": str(exc),
            })
            continue

        # Both checks refer to the same registry record; keep required notices unique.
        for text in (edit_grant.get("attribution"), publish_grant.get("attribution")):
            if text and text not in required_attributions:
                required_attributions.append(text)
        for text in (edit_grant.get("disclosure"), publish_grant.get("disclosure")):
            if text and text not in required_disclosures:
                required_disclosures.append(text)
        checked.append({
            "asset_id": asset_id, "kind": kind, "source_id": source_id,
            "status": "scope_match_metadata_only",
            "source_url": publish_grant["source_url"],
            "evidence_ref": publish_grant["evidence_ref"],
        })

    status = "blocked" if errors else "ready_for_human_review"
    return {
        "status": status,
        "platform": platform.strip().lower(),
        "checked_at": (at or datetime.now(timezone.utc)).isoformat(),
        "assets": checked,
        "errors": errors,
        "required_attributions": required_attributions,
        "required_disclosures": required_disclosures,
        "review": {
            "permission_evidence_human_verification_required": True,
            "all_embedded_music_and_third_party_rights_review_required": True,
            "original_asset_declarations_human_confirmation_required": True,
            "human_edit_and_platform_policy_review_required": True,
            "approved_for_upload": False,
            "monetization_guaranteed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check declared visual assets against the source rights registry."
    )
    parser.add_argument("content_pack", type=Path, help="Structured JSON content pack")
    parser.add_argument("--rights-db", type=Path, required=True, help="SQLite rights registry")
    parser.add_argument("--platform", required=True, help="Intended publishing platform, e.g. youtube")
    parser.add_argument("--output", type=Path, default=Path("preflight_report.json"))
    args = parser.parse_args()
    try:
        pack = json.loads(args.content_pack.expanduser().read_text(encoding="utf-8"))
        registry = SourceRightsRegistry(args.rights_db.expanduser())
        report = preflight_content_pack(pack, registry, args.platform)
        output = args.output.expanduser()
        write_json_atomic(output, report)
        print(json.dumps({
            "status": report["status"],
            "output": str(output),
            "asset_count": len(report["assets"]),
            "blocked_count": len(report["errors"]),
            "approved_for_upload": False,
        }, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "ready_for_human_review" else 2
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Preflight not completed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
