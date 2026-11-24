# ARO Chat Startup & Identity Prompt

Copy this block as the first instruction in every new AI engineering chat.

---

## FIRST RESPONSE: CHAT TITLE AND IDENTITY

Before doing any engineering work:

1. Read this instruction and inspect the repository's `docs/CHAT_WORKSTREAM_REGISTRY.md` plus open pull requests.
2. Reserve the next unused `ARO-CHAT-NNNN` ID and one bounded `ARO-GTA-P0-NN` Workstream ID. Never guess an ID or reuse an active ID. If another chat has reserved it, choose the next free ID.
3. Your **very first response line** must be exactly this format, with a concise title describing the primary task:

   `Suggested chat title: ARO-CHAT-NNNN | <short task title>`

4. Use that same title in your PR body under **Chat title**. Keep the title stable for this chat.
5. Do not claim you renamed the ChatGPT conversation. The first-line title is a naming cue for ChatGPT's automatic title behavior; automatic naming is controlled by the ChatGPT app and cannot be guaranteed by this prompt. The owner may rename it manually if needed.
6. Immediately after the title line, state the allocated Chat ID and Workstream ID, then continue the requested engineering task. Do not stop after naming, ask the owner to rename it, or turn the naming instruction into the task itself.

## ENGINEERING EXECUTION RULES

- GitHub repository is the source of truth: `anmollodhi718Aro/the-aro-gta6-clip-engine`.
- Check the registry, open PRs, active branches, and recent commits before editing. Avoid duplicate or conflicting work.
- One chat owns one active bounded workstream. Work only in its own branch, based on the owner-designated integration/RC branch.
- Do not change the selected RC base, merge, retarget, deploy, publish, or perform destructive operations without explicit owner approval.
- Every PR must include Chat ID, exact chat title, Workstream ID, task, branch, base, starting SHA, changed files, commits, tests actually run, exact-head CI evidence, and honest status.
- Distinguish IMPLEMENTED, TESTED, CI_VERIFIED, WINDOWS_VERIFIED, REAL_MEDIA_VERIFIED, and COMPLETE. A commit or green badge alone is not proof of end-to-end success.
- Report duplicate-work checks and explain whether the work passed, failed, or remains unverified. Never invent test results or permissions.
- Keep the user's immediate acceptance target in view: run the authorized local clipping workflow and produce a valid MP4 from owner-provided/licensed media. Do not claim real-media verification until that output is actually generated and checked.

## TASK EXECUTION

After the first response line and identity allocation, begin the owner's requested task immediately. Provide concise evidence, links, changed files, commit/PR identifiers, tests and blockers. Do not spend the response explaining the naming mechanism unless asked.


## CURRENT PROJECT BASELINE — refreshed 2026-11-22

Before acting, treat the live repository, current PR heads, workflow logs, and this registry as authoritative. Historical chat summaries are context, not proof of current state.

### Current verified engineering state
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`; default branch: `main`.
- Current documented continuation chain includes PRs #66, #71, #75, #76, #78, #79 and #80; PR #77 is a parallel documentation line. Inspect live ancestry and exact heads before choosing a base.
- PR #79 (`ARO-CHAT-0036`) adds source-audio preflight. Its exact current head at the latest audit was `ff82349dd509b1dbdd32038e92fd9efb4dc5fa36`.
- PR #80 (`ARO-CHAT-0037`) adds a locally generated synthetic MP4 render smoke test. Its audited head was `722945ba162a274b3ff78b5e5d472c97e7269a23`, stacked on PR #79.
- GitHub Actions run #44947413047 passed on PR #80 head: Ubuntu and Windows jobs each compiled and ran 288 tests; both also generated a synthetic MP4 and validated its video/audio metadata with FFprobe. Run #44947144076 passed the same 288-test suite on Ubuntu and Windows for PR #79 head.
- Synthetic fixtures are locally generated test patterns and tones only. They are NOT GTA 6 footage, do not establish real-media compatibility, and do not satisfy first-real-clip acceptance.
- PR #79 and #80 were OPEN / DRAFT / UNMERGED at the latest audit. Recheck before acting; do not infer they remain unchanged.

### First real GTA 6 clip: acceptance gate
The first real clip is NOT COMPLETE and remains blocked until all of the following are evidenced:
1. Owner/creator-authorized source recording or export is actually received through an authorized transfer path.
2. Permission evidence records the granting identity, asset/source, permitted processing and publishing scopes, applicable expiry/revocation terms, and a durable reference. Permission to process does not imply permission to publish or monetize.
3. Local intake confirms the file is present, non-empty, has video and required audio streams, valid duration, and sufficient output space.
4. Owner-approved clip bounds and render intent are recorded before execution.
5. A real MP4 is rendered locally and FFprobe validates the output streams, duration, and expected media properties.
6. The MP4 is played back and reviewed by the owner; acceptance is recorded.
Do not label REAL_MEDIA_VERIFIED or COMPLETE before every required step has evidence.

### Security, rights, and owner approval boundaries
- Keep public publishing disabled until uploader identity is bound to the authenticated channel owner and durable per-clip approval is enforced.
- Issue #68 has two parallel draft implementations: PR #82 (ARO-CHAT-0039), which has exact-head Ubuntu/Windows CI success, and PR #83 (ARO-CHAT-0038), which adds Google OIDC subject and visibility-bound approval but still needs exact-head CI. Do not merge both independently; the project owner must select or consolidate one canonical implementation. Keep the issue open and the gate unresolved until owner review and approved integration. No real upload or public publishing is authorized by either implementation task.
- Never scrape, stream-rip, download, or process unapproved third-party media. Use only owner-provided or otherwise explicitly licensed media within its documented scope.
- Do not expose secrets, tokens, private credentials, or sensitive account data in commits, logs, prompts, or PRs.
- Broad repository access or a general statement of permission does not waive action-specific approval gates.

### Known reconciliation items
- PR #72 and PR #74 both historically claimed ARO-CHAT-0031 / ARO-GTA-P0-31. Preserve both histories and reconcile attribution from PR bodies, commits, and registry evidence; never silently overwrite or delete either.
- PR #77 and #78 historically overlap as parallel documentation branches. Compare trees and ancestry before integration; do not merge both blindly.
- Earlier dependency sequence recorded as #18 → #66 → #71 → #75 → #76 → #78 → #79 → #80, with #77 parallel to #78. Revalidate the live graph each session.
- ARO-CHAT-0001 historical PR attribution remains unverified. Do not invent exact ownership.
- Chat serials #0001–#0008 are historical registry entries, distinct from the newer #0036–#0037 workstream records. Do not conflate these numbering groups.

### Required next-action order
1. Re-audit live PRs, branches, issue #68, exact CI heads, and dependency graph.
2. Reconcile duplicate attribution (#72/#74) and overlapping docs (#77/#78) without destructive changes.
3. Resolve the authenticated uploader/approval design only under a dedicated approved security task.
4. Obtain the authorized source media and permission evidence.
5. Run the local first-real-clip workflow, FFprobe validation, playback, and owner acceptance.
6. Only then prepare release integration. Merge, close, retarget, deploy, upload, publish, or delete only with explicit action-specific owner approval.

### Reporting format for every continuation
Report each item as one of: RESERVED, IN_PROGRESS, IMPLEMENTED, TESTED, CI_VERIFIED, WINDOWS_VERIFIED, REAL_MEDIA_VERIFIED, BLOCKED, or COMPLETE. Include exact SHA/run/test counts and distinguish hosted Windows CI from owner-device Windows verification. List unverified work explicitly. Never report a synthetic MP4 as a GTA 6 clip.


### ARO-CHAT-0038 scoped security continuation — 2026-11-22
- A dedicated owner authorization has been supplied for Issue #68's fail-closed authenticated channel-owner approval integration.
- Active workstream: ARO-CHAT-0038 / ARO-GTA-P1-38 on \`workstream/aro-chat-0038-authenticated-uploader-approval-2026-11-22\`; PR #83 targets PR #80's branch and the workstream branch was started from PR #81 head \`20a6645690935ac04054fc1a6564d8e6275daa3c\`.
- Preserve the draft-only boundary. No real upload, public publishing, credential handling beyond the local OAuth flow, merge, retarget or deployment is authorized by this engineering task.
- The uploader must verify the Google OIDC subject and destination channel from the same OAuth session, require a durable per-clip approval bound to the exact video hash, Google subject and channel, and re-check live publish permission immediately before the upload API call.
- A client-supplied reviewer string or legacy boolean is never identity authentication. Fail closed on missing/mismatched channel, clip, source, file hash, approval, permission, expiry or revocation.
- Use mocked API clients in tests; no test may perform a network upload. Keep public publishing disabled unless every authenticated owner, per-clip approval and source-rights gate passes.


## PRIVATE upload completion gate — refreshed 2026-11-24

For the current first-test upload priority:
- PR #289 (PRIVATE-only guard ordering) and PR #295 (isolated destination profiles) have recorded Ubuntu and hosted Windows CI success on their exact heads; verify current live heads/runs before relying on that evidence.
- PR #295 is stacked on PR #289, which is stacked on PR #280 and the authenticated uploader workstream. Do not merge these stacked PRs independently or bypass their ancestry.
- Each destination must use its own locally authorized OAuth session, verified Google OIDC subject, exact channel ID returned by YouTube channels.list(mine=true), token file, and separate approval record bound to the exact MP4 SHA-256. Never infer channel IDs from public handles.
- The upload request must be PRIVATE-only. A successful request is not enough: require YouTube's response to include a video ID and status.privacyStatus == "private"; otherwise report upload state as UNVERIFIED and direct the owner to inspect YouTube Studio.
- Do not commit OAuth files, tokens, channel IDs, private approvals, or media. Never ask the owner to paste secrets into chat.
- Automated tests must mock OAuth and YouTube API clients. No test may perform a live upload.
- Distinguish code/CI completion from environment setup and live acceptance. Real upload still requires local OAuth configuration, verified source publish rights, exact per-channel approval, and an actual private-visibility confirmation. Public publishing remains a separate owner action.


## ARO-CHAT-0134 CI closeout — 2026-11-24
- PR #299 implementation head `d4ca7042ff8bfbd00070f801d374b6292feddfda` passed run #45391987858 on hosted Ubuntu and Windows. Both compiled, passed the same 332 tests, and passed synthetic MP4/FFprobe validation.
- Both jobs used merge SHA `4a22ec0cdf15cbc78b17543c21e3b0f75a8f16b3` with base PR #295 head `cf731cabda8a045d39457f0eef800dbdb051e75e`; raw-head-only checkout NOT DEMONSTRATED.
- Synthetic-only: no GTA 6 footage or third-party media; publishing disabled; manual review required. PR #299 remains draft/open/unmerged; independent security review NOT RECORDED.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Live uploads/public publishing remain disabled. OAuth/channel verification, source-rights evidence, per-clip approval, owner-device verification and real private-upload acceptance remain NOT VERIFIED.


## Destination profile storage boundary — 2026-11-24
- Destination profile config must resolve to a file directly inside the repository's `.secrets/` directory. The loader rejects configs whose resolved parent is elsewhere, including symlink targets outside `.secrets/`.
- Profile-specific OAuth tokens remain under `.secrets/tokens/<profile>.json`. Never commit profile config or token files.
- Regression test rejects an otherwise valid profile file outside `.secrets/`; CI for this new head is pending.


## ARO-CHAT-0197 current continuation — 2026-11-24

- Continue from PR #299 head `758ae2d44e04b9a875a2a85aa153f0407a209766` on a separate draft-only branch. Do not merge or retarget the stacked PR chain.
- Latest observed run #45393428557: Ubuntu passed; hosted Windows failed 1 of 334 tests because a test compared a `Path.resolve()` canonical path against an un-resolved temporary path (`RUNNER~1` versus `runneradmin`). The fix updates the test expectation to use the resolved `.secrets` parent; do not weaken production path validation.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. No live upload or public publishing until the authenticated owner/channel approval design is selected, integrated, independently reviewed, and locally verified.
- PR #299 and this follow-up must be validated on their latest exact heads. Synthetic MP4/FFprobe checks are not real GTA 6 media acceptance.


### ARO-CHAT-0197 follow-up — 2026-11-24
- Test-only continuation commit `8269505c423e50c7460335f5ca776f250b695aa0` now asserts canonical token paths for both configured destination profiles, using the resolved `.secrets` parent. Production path enforcement is unchanged.
- Registry/startup documentation update follows in commit `7dad8ec0bf0140dd522369de846e10efe7436bb6`; exact-head Ubuntu and hosted-Windows CI remains pending.


## ARO-CHAT-0197 PR #300 current continuation — 2026-11-24
- Draft PR #300 is OPEN / UNMERGED. Current head before this documentation refresh: `02b5e7c16077d31e9cee1950cc5c379339c5baff`.
- Test-only path assertion compares both profile token paths against the strictly resolved `.secrets` parent. Production path validation is unchanged.
- No commit-associated CI run was found for that head; exact-head Ubuntu and hosted-Windows CI remains PENDING. No local tests run in this connector session.
- PR #300 review submissions and inline review threads are empty; independent review NOT RECORDED. Do not merge or retarget. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.


### ARO-CHAT-0197 live-head reconciliation — 2026-11-24
- Live PR #300 metadata reports branch `workstream/aro-chat-0197-pr299-windows-path-regression-fix-2026-11-24`, head `83445d763ebce065140a0f7a19ac75c42a761d48`, and base SHA `152de0e3cecbfe2be2569c46db14e5c9c67506a2`. Earlier notes naming `02b5e7c16077d31e9cee1950cc5c379339c5baff` describe the preceding docs commit, not the current head.
- Exact-live-head workflow lookup and combined status returned no checks for `83445d763ebce065140a0f7a19ac75c42a761d48`; Ubuntu and hosted-Windows CI remain PENDING. Do not claim the older PR #299 run validates PR #300.
- Keep PR #300 draft/open/unmerged. No local tests, OAuth, credentials, real-media processing, upload, publishing, merge, retarget, or deployment occurred. Issue #68 remains open and unresolved; live uploads/public publishing stay disabled.


## ARO-CHAT-0197 latest live-head reconciliation — 2026-11-24
- PR #300 remains OPEN / DRAFT / UNMERGED. Live head: `68b62198572117d22fe4072a8e3a48abf05cadd6`; base branch: `workstream/aro-chat-0134-private-upload-response-verification-2026-11-24`; recorded base SHA: `152de0e3cecbfe2be2569c46db14e5c9c67506a2`.
- The previous recorded head `83445d763ebce065140a0f7a19ac75c42a761d48` is stale. Base-to-head comparison reports 10 commits ahead / 5 behind with merge base `758ae2d44e04b9a875a2a85aa153f0407a209766`; do not rebase or retarget automatically.
- No commit-associated workflow run was returned for the current head. Exact-head Ubuntu and hosted-Windows CI are PENDING / NOT VERIFIED. Local tests were NOT RUN in this connector session.
- The current diff remains limited to the profile-path regression test and the registry/startup documentation. Both expected token paths use the strictly resolved `.secrets` parent; production uploader enforcement is unchanged.
- Independent review is NOT RECORDED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled. No OAuth, credentials, real media, API upload, publishing, merge, rebase, retarget, deployment, or destructive action.


## ARO-CHAT-0197 path-boundary hardening continuation — 2026-11-24
- The destination-profile loader now rejects a symlinked `.secrets` parent before resolving the config file. It preserves the base branch's exact repository-root/.secrets containment check and OAuth token-directory symlink guard.
- The loader was aligned with the current PR #299 base implementation; profile fixture tests now provide their isolated `repository_root`.
- Added tests for config-file, `.secrets` directory, and OAuth `tokens/` directory symlink escapes.
- Commits: `6c21c0977a6a9ec7643306f14fe7edf26f81d592`, `848cdb1447743257e9a00ac7fa84da22c58a9acf`, `e10070cc0a9ff167922649ce2293bb6a5a3ab3ae`, `a1c785ad7a54121732d3d59289054090ee892d96`.
- Exact-head Ubuntu/Windows CI is PENDING and local tests are NOT RUN. PR #300 is still DRAFT / OPEN / UNMERGED and currently reported non-mergeable. Do not merge, rebase, or retarget automatically. Issue #68 remains open; keep uploads and public publishing disabled.


## ARO-CHAT-0201 continuation — 2026-11-24
- Current consolidated private-upload hardening is Draft PR #311 on `workstream/aro-chat-0201-consolidated-private-upload-security-2026-11-24`, based directly on PR #295 head `9f6cdc10bc77e99d6a9399f3c8a1505e18a87ab0`.
- It consolidates PR #299's YouTube PRIVATE response verification and PR #300's destination-profile path/symlink hardening and Windows canonical-path tests, avoiding the stale diverged #299 → #300 branch ancestry.
- Issue #68's corrected authenticated OIDC/channel-owner gate, exact clip/source/hash approval, and source-rights checks are present in the PR #295 base ancestry. Do not use historical PR #83 head `f66f6406a496d08e3e85972010f1f52d831298ab` as current code; that historical snapshot contains a recursive verifier defect.
- PR #311 exact-head CI must pass on both Ubuntu and Windows before acceptance. Issue #68 stays OPEN until independent security review and owner-device OAuth/channel verification. No live upload or public publishing without separate explicit owner action.


## ARO-CHAT-0201 latest continuation — 2026-11-24
- Independent review of PR #311 found two security regressions: removed case-insensitive destination-profile name uniqueness and removed profile-specific approval-record directory enforcement.
- Both guards are restored. Regression tests now cover case-colliding profile names and approval-record directory isolation/required-path behavior.
- Production guard commit: `30229510555805bb9c723c66403bb5695ffa726f`; test commit: `566e19440add291fd0ceedc48aee662e314cf697`.
- The previous green run #45418114502 is pre-fix evidence only. Verify Ubuntu and hosted-Windows CI against the final PR #311 head; do not reuse the earlier run as proof.
- Keep PR #311 draft/open/unmerged. Issue #68 remains open pending independent security review and owner-device OAuth/channel verification. No live upload or public publishing.

### Next authorized task
Inspect exact-head Ubuntu/Windows CI and independently review the full uploader/approval diff. Fix any newly evidenced defects on the same draft branch, update this prompt and the workstream registry, and do not merge, deploy, run OAuth, or upload media.


## ARO-CHAT-0215 — bind uploaded bytes to the approved snapshot (2026-11-24)
- Finding: the approval record binds consent to the source SHA-256, but a resumable filename-based media client can reopen a mutable original path after the final approval check.
- Fix: open the source as a regular file, compare path/descriptor identity, copy from that descriptor into a private temporary directory, verify stable file metadata and byte count, mark the snapshot read-only, and use the snapshot for both approval-hash checks and MediaFileUpload.
- Regression test mutates the original source immediately before the mocked insert and asserts the media body still references the original approved bytes.
- Branch: workstream/aro-chat-0215-verified-upload-byte-snapshot-2026-11-24; based on PR #311 head 67e6d4290fee795fb8ba6fd0e926107ea7f0eb81. Code commits 1fefe87ef47dd4be723cab8ba9424b31156e46c1 and f14f00758fad5cd400f4a1efeacb9e04256a279d; test commit 7d8fd5c85f4171e702cada1d0e6c9fcece2a494b.
- Local tests NOT RUN; exact-head Ubuntu/hosted-Windows CI PENDING. No OAuth, real media, upload, merge, deployment or publishing. Keep Issue #68 open and public publishing disabled.


- FIFO follow-up: the snapshot source open now includes O_NONBLOCK where supported, so a source pathname swapped to a FIFO after lstat cannot hang the uploader. A platform-aware regression test covers the race; fresh exact-head CI is pending.


### ARO-CHAT-0215 CI closeout — 2026-11-24
- Code/test head `1c380a2e311abbd5b818a398d0f0a70011f547d4` passed Actions run #45427291297 on merge ref `938dd9ef262b848fbc5f236601f8466171d77b9a`: Ubuntu 342 passed; hosted Windows 342 executed, 341 passed and FIFO-specific test skipped because `os.mkfifo` is unavailable; synthetic MP4/FFprobe passed on both.
- Regression for changing the original source before mocked insert passed on both platforms. FIFO-race regression passed on Ubuntu and was skipped only on hosted Windows due to platform capability.
- No GTA 6/third-party media, OAuth, network upload, or publishing. Raw-head-only CI NOT DEMONSTRATED. This docs closeout changes the head and needs fresh exact-head CI.


### ARO-CHAT-0215 latest continuation — approval-record read hardening
- PR #328 remains the active draft branch: `workstream/aro-chat-0215-verified-upload-byte-snapshot-2026-11-24`, based on PR #311 head `67e6d4290fee795fb8ba6fd0e926107ea7f0eb81`.
- Independent review found that the inherited approval reader followed symlinks and did not bind the pre-open path to the opened descriptor. Fixed on this same branch; symlink, path-replacement, directory and FIFO regression tests added.
- Commits: production `e20445398a69e2bffb3d58401f3f5a7b322bf10d`; tests `8f6577db86580d4ea90c55736e619262d02302bc`.
- Prior run #45426822957 validated the previous head only (341 tests on each hosted OS; synthetic MP4/FFprobe; merge-ref checkout). It does not validate the new commits. Inspect the latest PR head's Actions jobs and logs before claiming CI_VERIFIED.
- Next: audit exact latest-head Ubuntu/Windows CI and complete independent review of PR #328. Keep PR draft/open/unmerged. Issue #68 remains OPEN. No OAuth, credentials, real media, network upload, merge, deployment or publishing; public publishing remains disabled.


### ARO-CHAT-0215 post-open approval-path identity follow-up
- The durable approval reader now performs a second pathname `lstat()` after open and requires a regular file with the same device/inode as the opened descriptor. This protects the fallback when `O_NOFOLLOW` is unavailable.
- Added same-inode symlink substitution regression test. Production commit `d40aac24f08ec3ae7f5660fdc3aa73bf0e2598bb`; test commit `57dedee38b353a75e54f7aca89526604d8537b49`.
- Exact-head Ubuntu/hosted-Windows CI remains PENDING after branch updates. No OAuth, real media, upload, merge, deployment or publishing.



### ARO-CHAT-0215 combined CI closeout — 2026-11-24
- PR #328 head `e1dd08c12d81e3a5c56eef65784955f0e55d4021` passed run #45428060156 on merge ref `b4adb085f8976e79bb70356b4314dbd450b23416` (base `67e6d4290fee795fb8ba6fd0e926107ea7f0eb81`).
- Ubuntu: compile, 348 tests, synthetic MP4/FFprobe passed. Hosted Windows: compile, same 348 tests, 345 passed and 3 FIFO-only tests skipped because `os.mkfifo` is unavailable; synthetic MP4/FFprobe passed.
- Both regression paths passed: original source mutation at insert time, and same-inode approval symlink substitution after open. FIFO race test passed on Ubuntu and skipped on Windows due to unavailable FIFO creation.
- Both jobs ran the same suite, not 696 unique tests. Raw-head-only checkout NOT DEMONSTRATED. Synthetic-only; no OAuth/upload/publishing. Independent review NOT RECORDED; owner-device and real-media PRIVATE acceptance NOT VERIFIED.


## Current continuation — ARO-CHAT-0218 (2026-11-24)
- Workstream: ARO-GTA-P1-218; restore approved-upload media-handle cleanup on the latest PR #328 head.
- Branch: `workstream/aro-chat-0218-current-head-media-cleanup-2026-11-24`; base / starting SHA: `5ef44f391720966138b2eec1815dd223fb345dbd`.
- Finding: latest PR #328 head had removed the Windows-safe `MediaFileUpload._fd` close-before-snapshot-cleanup sequence present in stale PR #333; PR #335's request-failure test was stacked on that stale branch.
- Changes: restore stream close in a nested `finally` before snapshot-directory cleanup; extend the approved-source-mutation test and add a mocked request-failure cleanup regression.
- Local tests NOT RUN. New-head Ubuntu/hosted-Windows CI must be inspected independently. No OAuth, real media, upload, publishing, merge, rebase, retarget, deployment, or destructive action. Issue #68 remains OPEN; keep live uploads/public publishing disabled.


### Current continuation handoff — ARO-CHAT-0218
- Continue from PR #339 branch `workstream/aro-chat-0218-current-head-media-cleanup-2026-11-24`.
- Latest test commit: `a07cf1d0e1023f6291cf69bb6998c4f43c972fdf`. Added a mocked close-failure regression proving the nested `finally` removes the approved-byte snapshot even when media stream closure raises.
- Inspect exact-head Ubuntu and hosted-Windows CI before marking CI_VERIFIED. Local tests, owner-device Windows, OAuth, real-media PRIVATE acceptance, and independent security review are NOT VERIFIED.
- Do not merge, deploy, access credentials, perform live uploads, or enable public publishing. Issue #68 remains OPEN.


### ARO-CHAT-0218 latest code/test handoff
- PR #339 latest test commit: `cc4dca770655a7bd69d767f9cb164d133e00eafd`.
- Close-failure regression asserts exactly one close attempt, propagation of the synthetic close error, closed underlying stream, removal of the approved-byte snapshot, and exactly one mocked insert.
- Exact-head Ubuntu/hosted-Windows CI is NOT VERIFIED (no associated run/status returned); local tests and independent review are NOT RECORDED. Keep PR #339 draft/open/unmerged; no OAuth, real media, upload, deployment, or publishing. Issue #68 remains OPEN.


### Current ARO-CHAT-0218 handoff — PRIVATE-only guard
- PR #339 branch: `workstream/aro-chat-0218-current-head-media-cleanup-2026-11-24`.
- Uploader now rejects UNLISTED/PUBLIC in both metadata validation and CLI; PRIVATE is the only supported upload visibility. Tests cover rejection. Documentation corrected to remove obsolete public/unlisted approval instructions.
- Code commit `e21f377583df944f5489e7d6a359bb5d2d1e6438`; test commit `598c9c488c34143c6cb8c0a9d86208e3e7ef74b1`; docs commit `51dbcdf38c59c6f74d239014fbb92019b6d50201`.
- CI run #45433283842 cancelled before compile/tests; run #45433336438 pending. Exact-head CI NOT VERIFIED. PR #339 draft/open/unmerged; parent PR #328 currently non-mergeable. Independent review NOT RECORDED; issue #68 OPEN.
- Do not merge, rebase, retarget, access OAuth credentials, upload real media, deploy, or publish. Continue code/tests and evidence collection only.


### Latest CI handoff — ARO-CHAT-0218
- Private-only uploader guard remains in place. Run #45433336438 exposed a stale error-message assertion; updated it in commit `52c168d4a389ab7a99bff5f660708382d00079df`.
- Exact-head run #45433572590 is in progress on Ubuntu and hosted Windows. Verify both jobs before claiming success. PR #339 remains draft/open/unmerged; no live uploads or publishing.


## Current continuation — ARO-CHAT-0219 (2026-11-24)
- Task: revalidate the current rights-preflight report immediately before the YouTube upload API side effect.
- Branch: `workstream/aro-chat-0219-revalidate-rights-report-before-upload-2026-11-24`, based on PR #339 functional/docs head `b0a5e3e1adcff9f7a2f3715b6ba7a0c138a50722`.
- Finding: the uploader repeated current rights-registry checks but reused an earlier in-memory rights report; newly added source-bound assets could be omitted from the final check.
- Fix and regression committed: `56685d4edf88af8d15b2390283752792984427a5`, `70b86a1ead7f3f4c6c466dc79684041aac08ea18`, and assertion correction `0e3d54632d142d64d609aef6641ba6d295615941`.
- Local tests NOT RUN; this branch's exact-head Ubuntu/hosted-Windows CI PENDING; independent security review NOT RECORDED.
- Next: inspect this branch's own exact-head CI and review the full uploader/approval lineage. Keep PR draft/unmerged; Issue #68 OPEN; no OAuth, credentials, real media, network upload, merge, deployment, or publishing. Public publishing remains disabled.


### PR #344 current-head and ancestry audit — 2026-11-24
- Draft PR #344 created against PR #339's branch; PR #344 head at audit: `f9688ebce4c1b8da646f1cf8289a92b1936a03c8`.
- PR #344 head-associated workflow lookup returned zero runs; exact-head Ubuntu/hosted-Windows CI is PENDING / NOT VERIFIED.
- The base branch advanced from starting SHA `b0a5e3e1adcff9f7a2f3715b6ba7a0c138a50722` to `6204a3979b8753919e3f983ce42a3777b3215d87` by 12 documentation-only commits. Compare reports PR #344 head 6 commits ahead and 12 behind the current base, with merge base at the starting SHA; status DIVERGED.
- Preserve PR #344 as DRAFT / OPEN / UNMERGED. No automatic rebase or retarget. Reconcile the documentation-only parent advancement with owner approval before ancestry changes.
- Local tests NOT RUN. Independent security review NOT RECORDED. Issue #68 remains OPEN. Keep live uploads/public publishing disabled.


## ARO-CHAT-0223 current continuation — PR #344 CI assertion correction (2026-11-24)
- Chat ID: ARO-CHAT-0223; Workstream: ARO-GTA-P1-223.
- Follow-up branch `workstream/aro-chat-0223-pr344-ci-assertion-fix-2026-11-24`, based on PR #344 exact audited head `d2e057734517c1dfb3be994eb7268580f1f173a4`.
- PR #346 run #45441375437 exposed the same test-only assertion mismatch on Ubuntu and hosted Windows: actual rejection is `no recorded rights for source source-2`; stale test expected `no recorded rights for source-2`.
- Corrected the test expectation only; production uploader and fail-closed rights behavior are unchanged. Commit `9e349ae9fa6d66832b8d030e2ffe3bef55cdf35d`.
- Next: verify exact-head Ubuntu and hosted-Windows CI for this branch, then independently review the complete rights/uploader security lineage. Local tests NOT RUN. No OAuth, credentials, real media, upload, merge, rebase, retarget, deployment, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.


## ARO-CHAT-0224 independent uploader security lineage audit — 2026-11-24
- Documentation-only audit branch `workstream/aro-chat-0224-independent-uploader-security-lineage-audit-2026-11-24`, based on PR #350 head `b6d712a6438a132c3d8ca245b0a804bf8b929550`.
- PR #350 exact-head run #45442036637 passed Ubuntu and hosted-Windows jobs, including compile, unit tests, and synthetic MP4/FFprobe. No raw-head-only or real-media acceptance is claimed.
- Independent review found PR #344 / #350 still uses `Credentials.from_authorized_user_file()` after a symlink check; the separate PR #342 no-follow descriptor loader is not integrated into this branch. Treat the OAuth token path race as a blocker.
- PR #342 and PR #344 are separate implementations sharing ARO-CHAT-0219 attribution. Preserve both histories and require owner selection before consolidation. No rebase, retarget, merge, OAuth, real media, upload, or publishing.
- Report: `docs/ARO_CHAT_0224_UPLOADER_SECURITY_LINEAGE_AUDIT.md`. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
