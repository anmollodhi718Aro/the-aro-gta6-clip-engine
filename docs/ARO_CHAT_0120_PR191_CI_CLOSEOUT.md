# ARO-CHAT-0120 | PR #191 Exact-Head CI Closeout

Date: 2026-11-24

## Scope and attribution

- Chat ID: ARO-CHAT-0120
- Workstream ID: ARO-GTA-P1-120
- Parent implementation PR: [#191](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/191)
- Branch: `workstream/aro-chat-0120-pr176-ci-test-contract-fix-2026-11-24`
- Audited head: `35d77ce48ec6fbd2f86503a3f45f3ba88d325efc`
- Base: `workstream/aro-chat-0109-issue68-pre-oauth-bounded-copy-2026-11-24`
- Base SHA: `2a83ce65706d0a8ccce0d5eaf56651fb9f5caa69`
- CI run: [#45256856022](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45256856022), run 1015, SUCCESS

## Exact-head evidence

The workflow run is associated with the exact PR head above. Both jobs completed successfully:

- Ubuntu job #137980832512: source compilation passed; 338 unit tests passed in 4.965s; synthetic MP4 render and FFprobe validation passed.
- Hosted-Windows job #137980833158: source/test compilation passed; 338 unit tests passed in 14.816s; synthetic MP4 render and FFprobe validation passed.
- Both jobs checked out `refs/remotes/pull/191/merge` at merge SHA `811195d53fa14c7a54d892204ae056b8bac286ac`, merging audited head `35d77ce48ec6fbd2f86503a3f45f3ba88d325efc` into base `2a83ce65706d0a8ccce0d5eaf56651fb9f5caa69`.
- Raw-head-only checkout is NOT DEMONSTRATED. These are successful merge-ref CI results.
- Both platforms ran the same 338-test suite; this is not 676 unique tests.
- Synthetic reports identify locally generated test patterns/tones, `gta6_footage_used=false`, `publishing_enabled=false`, and `manual_review_required=true`. Synthetic output is not GTA 6 footage or real-media acceptance.

## Review and implementation disposition

- PR #191 remains OPEN / DRAFT / UNMERGED; GitHub reported mergeable=true at inspection.
- PR review submissions and inline review threads were empty at inspection.
- Changed files in PR #191: `docs/ARO_CHAT_0120_PR176_CI_TEST_CONTRACT_FIX.md`, `docs/ARO_CHAT_STARTUP_PROMPT.md`, `docs/CHAT_WORKSTREAM_REGISTRY.md`, and `tests/test_youtube_upload.py`.
- The follow-up regression now asserts staging cleanup before upload-request construction, mutates the original source after staging, and verifies the immutable captured bytes are still the bytes consumed by the upload stream.
- Local tests were NOT RUN in this connector session. CI evidence is from GitHub Actions only.

## Safety and remaining gates

- Issue #68 remains OPEN / UNASSIGNED / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
- This closeout did not use OAuth credentials, tokens, real media, network upload, or public publishing.
- No merge, retarget, deployment, workflow rerun, or destructive action was performed.
- Hosted Windows CI is not owner-device Windows verification. Owner-device validation, independently reviewed authenticated-uploader integration, owner selection of a device-appropriate `--max-upload-bytes`, authorized real media, and first-real-clip acceptance remain outstanding.

## Status

- PR #191 exact-head merge-ref CI: CI_VERIFIED.
- Raw-head-only CI: NOT DEMONSTRATED.
- Owner-device Windows: NOT VERIFIED.
- Real-media acceptance: NOT VERIFIED.
- Project release / first real GTA 6 clip: NOT COMPLETE.
