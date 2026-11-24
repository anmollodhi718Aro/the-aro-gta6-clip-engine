# MVP Usage

The local MVP analyzes permitted chat-event records, creates reviewable candidate plans, records human decisions, and renders local MP4 clips from authorized media. It does not connect to platform APIs, download video, upload, or publish.

## Source registry

Create a JSON file with schema_version 1 and a sources array. Each source contains source_id, creator_name, permission_evidence_ref, optional owner_contact/permitted_platforms/attribution, and a permission object with source_id, granted_by, scopes, granted_at, expires_at, and revoked_at. Keep private evidence itself outside Git; store only a durable reference. Never store tokens or passwords.

Scopes are separate: analyze_chat permits event analysis; edit_media permits local video editing. Expiry and revocation are checked at use time. The example registry is synthetic only and does not authorize real media.

## Analyze events

    python -m backend.app.cli events.json --registry my_sources.json --source-id my-channel --output clip_plan.json

The analyzer normalizes timestamps to UTC, rejects events outside active analyze_chat permission, caps batches at 10,000 events and text at 4,000 characters, and deduplicates identical event IDs. Conflicting duplicates fail closed. Inline permission JSON remains available for synthetic tests.

Candidates contain a stable candidate_id, score, evidence, clip timestamps, and needs_review status.

## Review a candidate

    python -m backend.app.review_cli clip_plan.json --candidate-id CANDIDATE_ID --decision approved --reviewer local-reviewer --ledger review_ledger.json

Decisions are append-only, one final decision per candidate. The reviewer field is a local label, not an authenticated identity. Review approval does not authorize upload or publication.

## Render an authorized clip

    python -m backend.app.render_cli input_video.mp4 review_clip.mp4 --start 12.5 --duration 35 --registry my_sources.json --source-id my-channel --confirm-rights

Rendering requires an active registry edit_media scope plus explicit rights confirmation for the exact file. Duration is limited to 180 seconds, existing outputs are not overwritten, and temporary output is cleaned after failures.

Before editing or distributing real footage, check permission for that exact asset and separately check game, music, guest, and platform rights. A registry is an operational control, not universal rights clearance.

## Tests

    python -m unittest discover -s tests -v

CI generates a synthetic moving test pattern, renders a short MP4, and checks duration with FFprobe on Ubuntu and Windows. Synthetic output is not real GTA 6 footage.
