# THE ARO GTA 6 Clip Engine

Creator-first tooling for preparing short highlights from media and event data the operator owns or is explicitly authorized to process.

## Local MVP core

- Durable local source registry with permission evidence references, separate scopes, expiry, and revocation.
- Permission-gated event normalization to UTC, bounded batch/text sizes, and duplicate-event handling.
- Deterministic chat-spike candidates with stable IDs, evidence, scores, and review status.
- Append-only human review decisions.
- Local FFmpeg rendering guarded by active source-registry edit_media permission and explicit rights confirmation.
- Synthetic moving-video render and FFprobe checks in Ubuntu/Windows CI.

This MVP does not connect to live platform APIs, scrape streams, call AI providers, upload, or publish. Dashboard, Android client, live ingestion, OAuth upload, and hosted services are separate future phases.

## Quick start

With Python 3.11+:

    python -m unittest discover -s tests -v
    python -m backend.app.cli examples/sample_events.json --registry examples/source_registry.json --source-id synthetic-demo-stream --output clip_plan.json
    python -m backend.app.review_cli clip_plan.json --candidate-id CANDIDATE_ID --decision approved --reviewer local-reviewer

The included registry is synthetic test data only. Replace it with a record backed by real permission evidence before processing real creator data.

## Render a local review clip

    python -m backend.app.render_cli input_video.mp4 review_clip.mp4 --start 12.5 --duration 35 --registry my_sources.json --source-id my-source --confirm-rights

The renderer refuses unregistered or inactive edit_media permission, requires explicit rights confirmation, limits clips to 180 seconds, and never downloads or uploads media.

## Rights and safety

- analyze_chat permission does not imply edit_media permission.
- Creator permission does not automatically clear game, music, guest, or platform rights.
- Local review approval is not upload or publishing approval.
- Public uploads remain disabled until authenticated channel-owner identity, exact clip/source approval, and current rights checks are implemented and independently verified.
- Never store credentials, OAuth tokens, or passwords in the registry.

See docs/MASTER_PLAN.md, docs/COPYRIGHT_POLICY.md, docs/MVP_USAGE.md, and docs/TESTING_PLAN.md.
