# ARO-CHAT-0324 | Verify Synthetic Smoke-Test Output Digest

Date: 2026-11-26

## Attribution
- Chat ID: ARO-CHAT-0324
- Exact title: ARO-CHAT-0324 | Verify Synthetic Smoke-Test Output Digest
- Workstream ID: ARO-GTA-P0-324
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Existing draft PR: #386
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Base branch: `workstream/aro-chat-0243-single-video-preflight-schema-guard-2026-11-25`
- Starting PR head: `61ad1309720b0bf738b6a47427a4ad973f75bfbc`

## Finding
The synthetic smoke harness validated that the renderer's reported SHA-256 was syntactically 64 lowercase hexadecimal characters, but did not independently hash the produced MP4. A faulty or mocked renderer could therefore return a plausible but incorrect digest and the harness would still report PASS.

## Changes
- Independently stream-hash the rendered MP4 with SHA-256 after checking that the output exists and is non-empty.
- Require the independently computed digest to exactly match the renderer's reported digest before returning PASS.
- Update the successful test fixture to report the actual digest of its generated output bytes.
- Add a regression where the renderer returns a well-formed but incorrect digest; the smoke harness must reject it.

## Commits
- Production: `9efc07703673a2792c008e8696d89bd9a3077cb9`
- Regression: `53d0c42d9670c3f895bba19c134cbf8a11c8a675`

## Verification
- Static source edits committed to the existing PR #386 branch.
- Repository unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end smoke execution: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: PENDING / NOT VERIFIED.
- Independent review: NOT RECORDED.
- Authorized real GTA 6 MP4: NOT PROCESSED / NOT VERIFIED.

## Safety
- Synthetic fixtures only; no third-party or GTA 6 media used.
- No OAuth, credentials, upload, publishing, workflow retry/dispatch, merge, rebase, retarget, deployment, or destructive action.
- Keep PR #386 OPEN / DRAFT / UNMERGED and preserve its existing base and ancestry.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
