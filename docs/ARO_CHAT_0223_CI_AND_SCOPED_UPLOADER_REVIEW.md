# ARO-CHAT-0223 CI and scoped uploader review — 2026-11-24

## Scope
Record the CI evidence for PR #350 and a bounded code inspection of the PR #344 rights-report revalidation change and its uploader, owner-approval, and source-rights dependencies. This is an assistant inspection, not an independent external security review.

## CI evidence
- PR #350 branch: `workstream/aro-chat-0223-pr344-ci-assertion-fix-2026-11-24`.
- Test-only correction: `9e349ae9fa6d66832b8d030e2ffe3bef55cdf35d`.
- Latest recorded branch documentation tip at audit: `b6d712a6438a132c3d8ca245b0a804bf8b929550`.
- Associated Actions run: [45442036637](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45442036637), conclusion SUCCESS.
- Both Ubuntu and hosted Windows jobs checked out merge commit `74dbc1c`, which merged branch tip `b6d712a6438a132c3d8ca245b0a804bf8b929550` into base `d2e057734517c1dfb3be994eb7268580f1f173a4`.
- Ubuntu: 352 tests executed; job succeeded.
- Hosted Windows: 352 tests executed; job succeeded with 3 FIFO-only tests skipped because the platform does not expose FIFO creation.
- Both jobs compiled source/tests and passed the synthetic MP4/FFprobe check.
- Synthetic logs explicitly report no GTA 6 footage, no third-party media, `upload_performed=false`, `publishing_enabled=false`, and `manual_review_required=true`.
- Qualification: this validates the PR through its merge ref. Raw-head-only checkout was not demonstrated; do not describe this as a raw-head-only CI run. No real-media, OAuth, YouTube network upload, owner-device acceptance, or public publishing was tested.

## Scoped code inspection
Inspected:
- `backend/app/youtube_upload.py`
- `backend/app/youtube_owner_approval.py`
- `backend/app/rights_registry.py`
- the PR #344 production diff and its new rights-report mutation regression.

Observed safeguards in the inspected paths:
- Upload visibility is restricted to PRIVATE.
- OAuth identity is checked against a verified Google ID token and the configured YouTube channel.
- The authenticated owner is re-verified immediately before the upload request.
- Approval is bound to reviewer subject, destination channel, clip ID, source ID, exact video SHA-256, privacy, and an expiry timestamp.
- Approval record reads reject symlinks/non-regular files and compare descriptor/path identity.
- Upload bytes are copied to a verified snapshot; the resumable media client uses that snapshot and cleanup closes its retained stream.
- The current rights report is reloaded immediately before the API insert; exact clip/source IDs are rechecked and the clip source plus every source-bound asset are checked against current publish grants.
- The regression mutates the report to add an unregistered source-bound asset and asserts the YouTube insert is not called.

No additional confirmed defect was established by this bounded inspection. This is not a claim that the full security design is defect-free.

## Remaining limitations and gates
- The source-rights registry explicitly stores operator-supplied evidence metadata; it does not authenticate the grantor or determine legal sufficiency. Human verification of source permissions, embedded music, third-party assets, and platform policy remains required.
- PR #344's own current-head workflow lookup returned no associated run; its exact-head CI remains NOT VERIFIED.
- PR #350's run used a merge ref; raw-head-only checkout is NOT DEMONSTRATED.
- PR #344 review submissions and inline review threads were empty at inspection time. Independent external security review is NOT RECORDED.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Owner-controlled acceptance and channel/device verification remain outstanding.
- Local tests were NOT RUN in this connector session. Hosted CI evidence must not be described as local execution.

## Disposition
- PR #350 remains draft/open/unmerged.
- PR #344 remains draft/open/unmerged; no ancestry changes are authorized.
- No workflow retry/dispatch, OAuth session, credential access, real media, network upload, merge, rebase, retarget, deployment, or publishing was performed.
- Keep live uploads and public publishing disabled.


## Additional security finding: approval is not bound to the reviewed rights-report manifest

A deeper review of the approval path found a gap not covered by the existing “new unregistered source” regression:

- `write_owner_approval_record()` persists the clip ID, source ID, privacy, video SHA-256, reviewer Google subject, channel IDs, and timestamps. It does not persist a digest or immutable representation of the rights report or its asset manifest.
- The `--approve-clip` path loads the rights report and checks current publish grants, but the confirmation prompt displays only the authenticated channel and the clip/source approval phrase. It does not present the asset manifest or bind it into the approval record.
- At upload time, `require_current_owner_approval()` verifies the approval record against the clip/source/video/owner/privacy fields. Separately, `load_rights_report()` and `require_report_publish_permissions()` re-check the current report and grants.
- Consequently, if the rights report is changed after approval to add a source-bound asset whose source already has an active YouTube publish grant, the final rights check can pass while the durable owner approval still matches. The added asset was not necessarily part of the report the owner reviewed. The current regression covers an unregistered added source, which fails closed, but does not cover an already-registered added source.

**Disposition: P1 security finding; implementation remains blocked.** The approval must be bound to a canonical digest of the exact rights-report/asset manifest reviewed, and the upload path must compare that binding against the final report before the API insert. The approval prompt should expose the exact asset/source manifest being approved. Add a mocked regression that changes the report after approval by adding a separately registered, publish-authorized source and asserts that approval fails before YouTube insert.

This is a static-review finding, not an implemented fix or an independent external security review. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Do not change uploader/approval behavior until the owner explicitly authorizes this security remediation. Keep live uploads and public publishing disabled.
