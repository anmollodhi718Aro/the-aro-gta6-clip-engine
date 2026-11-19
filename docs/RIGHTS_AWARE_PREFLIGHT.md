# Rights-Aware Content Preflight

Run a local, fail-closed check before editing or publishing visuals named in a structured content pack.

## Input contract

The content pack may include a `visual_assets` array:

```json
{
  "visual_assets": [
    {"asset_id": "aro-weather-chart", "kind": "original"},
    {
      "asset_id": "creator-b-roll-01",
      "kind": "creator_authorized",
      "source_id": "creator-video-001"
    }
  ]
}
```

Use `kind: original` only for assets made by the channel or otherwise controlled by it. This declaration is not independently verified and still requires human confirmation.

For third-party assets, use `licensed` or `creator_authorized` and register the exact source in the SQLite rights registry. The preflight requires both `edit` and `publish` scope for the target platform. Missing, expired, revoked, future-dated, or out-of-platform grants block the pack.

## Run

```bash
python -m backend.app.content_preflight output/gta6_short.json \
  --rights-db state/rights.sqlite3 \
  --platform youtube \
  --output output/preflight_report.json
```

Exit code 0 means the recorded metadata matched and the pack is ready for human review. Exit code 2 means the check was blocked or could not complete. The report surfaces required attribution and disclosure text.

## Important limits

This checks registry metadata only. It does not authenticate a creator, validate permission evidence, clear game publisher/music/guest rights, or determine YouTube monetization eligibility. A successful report is not upload approval. Human review remains mandatory, and no upload/publishing is performed.
