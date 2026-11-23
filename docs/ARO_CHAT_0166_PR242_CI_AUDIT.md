# ARO-CHAT-0166 | PR #242 exact-head CI audit

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0166
- Exact title: ARO-CHAT-0166 | PR #242 Exact-Head CI Audit
- Workstream ID: ARO-GTA-P1-166
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0166-pr242-exact-head-ci-audit-2026-11-24`
- Starting SHA: PR #242 head `414fd4f7da94fdffcdd3261a5ea723b5f03290b3`
- Audited PR #242 current head at closeout: `dfb1e9390490806e44bad93fc661ddff0a551f54`
- Parent PR: [#242](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/242)
- Audit PR: [#246](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/246)
- Scope: documentation-only exact-head CI audit; no uploader behavior changes.

## Change under audit
PR #242 requires an explicit positive `--max-upload-bytes` value for every live upload, including direct `upload_video()` calls. Dry-run and approval-only operations retain the 256 MiB fallback. Regression tests cover missing explicit limits, direct-call rejection, and bounded-copy behavior. README documents the owner-selected device memory requirement.

## Current-head CI closeout
- PR #242 current head at closeout: `dfb1e9390490806e44bad93fc661ddff0a551f54`.
- Exact-head-associated Python CI run [#45278668116](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45278668116), run 1118, completed SUCCESS.
- Ubuntu job `138058372656`: compilation passed; 340 tests passed (4.934s); synthetic MP4/FFprobe passed.
- Hosted-Windows job `138058368900`: compilation passed; the same 340 tests passed (24.840s); synthetic MP4/FFprobe passed.
- Both jobs checked out PR #242 merge ref `refs/remotes/pull/242/merge` at merge SHA `ad80436817f46f8f36093ae95dc4eeed6cf0ce7e`, merging PR head `dfb1e9390490806e44bad93fc661ddff0a551f54` into base `cdcf7a4bef2728e3299e82bc88d376992ecec39d`. Raw-head-only checkout is NOT DEMONSTRATED.
- Both platforms ran the same 340-test suite, not 680 unique tests.
- Synthetic test source was a locally generated pattern/tone, 8-second source and 4-second output; `gta6_footage_used=false`, `third_party_media_used=false`, `publishing_enabled=false`, and `manual_review_required=true`. This is not GTA 6 footage or real-media acceptance.
- Current PR #242 combined status returned zero status entries; the successful workflow run and both job logs are the actual evidence.
- Earlier run #45278355448 (run 1113) checked out older PR head `414fd4f7da94fdffcdd3261a5ea723b5f03290b3` into merge SHA `4f3861c911beb77e45c05ca01a98768f16d9832e`. Ubuntu ran 340 tests and failed one CLI fixture; hosted Windows also ran 340 tests and failed the same fixture. This is superseded by the later current-head run #1118 and must not be presented as a current-head failure.
- Earlier-lineage run #45278418962 (run 1115) also had one Ubuntu fixture failure and Windows cancellation; it is not current-head evidence.
- The current head contains the corrected CLI test fixture passing explicit `--max-upload-bytes`; run #1118 verifies this later state.
- No local tests were run in this connector session.

## Bounded static review
- The CLI rejects `--upload` without an explicit limit before validation or OAuth.
- Direct `upload_video()` calls reject a missing limit before OAuth and validate the supplied limit as a positive integer.
- The byte ceiling is enforced both against the initial file size and during incremental staging, so source growth cannot exceed the configured budget before OAuth.
- Dry-run and approval-only operations retain the fallback; that fallback is not accepted for a live upload.
- No critical defect was identified in the bounded diff reviewed here. This is not a substitute for a separate human security reviewer or owner acceptance.

## Review and status
- PR #242 review submissions: none returned.
- PR #242 inline review threads: none returned.
- PR #242 conversation comments: none returned.
- Independent human security review: NOT RECORDED.
- PR #242 remains OPEN / DRAFT / UNMERGED.
- PR #246 is OPEN / DRAFT / UNMERGED; its own run [#45279477145](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45279477145) also passed 340 tests and synthetic MP4/FFprobe on Ubuntu and hosted Windows, checking out merge ref `refs/remotes/pull/246/merge` at `9e5243f6e6cccfa2706a5c2715689c88702bc903` (PR #246 head into base #242 head `dfb1e9390490806e44bad93fc661ddff0a551f54)). This corroborates the docs-only audit branch and the same base code tree; it is not a replacement for PR #242's own run #1118.
- Issue #68 remains OPEN. Keep live/public uploads disabled pending independent human security review, owner-controlled integration, owner-device verification, owner-selected device limit and separate authorized real-media acceptance.
- Hosted Windows CI is not owner-device Windows verification.

## Safety
- Documentation-only audit. No application/uploader/test/workflow behavior was changed.
- No OAuth, credentials/tokens, real media, network upload, public publishing, merge, rebase, retarget, deployment, workflow configuration change, or destructive action was performed.
