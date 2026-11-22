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


### Latest uploader byte-integrity follow-up — ARO-CHAT-0044
- Active bounded workstream: ARO-CHAT-0044 / ARO-GTA-P1-44 on branch workstream/aro-chat-0044-immutable-upload-payload-2026-11-22.
- Base is PR #88's exact head 7a1d9a9a66a7b16ed0632eee10189554f20d2aa6. This is a separate follow-up; PR #88 and the parallel PR #89/#90 branches are not modified.
- Security finding: even when the original source is staged and the staged file is hashed, the same file can be modified after the final hash check but before the YouTube client consumes its open stream.
- Fix: compare the durable approval against the SHA-256 of an immutable in-memory byte payload, and pass a stream over those exact bytes to MediaIoBaseUpload. The filesystem snapshot is no longer the upload source after capture.
- Mocked regression mutates the staged file after final approval checks and before the API mock consumes the media stream; it must prove the transmitted bytes remain the approved bytes. No network upload is used.
- PR #89 and PR #90 both claim ARO-CHAT-0043 / ARO-GTA-P1-43 for the same staged-snapshot hash-mismatch regression. Both exact-head Ubuntu and hosted-Windows CI runs passed; preserve both histories and wait for owner selection. Do not independently merge both.
- PR #87 and PR #91 contain parallel fixes for the same recursive Google OIDC verifier defect. PR #91 exact-head run 45014281658 passed Ubuntu and hosted Windows; do not independently integrate both verifier branches.
- ARO-CHAT-0044 code is IMPLEMENTED on its isolated branch; local tests were not run in this connector session; exact-head CI is pending. Keep PR draft-only, Issue #68 open until owner review, and all live uploads/public publishing disabled.
- No merge, retarget, deployment, credential/token access, real-media processing, live upload, public publishing, or destructive action is authorized by this follow-up.


### Latest uploader memory-budget follow-up — ARO-CHAT-0045
- Active bounded workstream: ARO-CHAT-0045 / ARO-GTA-P1-45 on branch workstream/aro-chat-0045-bounded-upload-memory-2026-11-22, based on PR #92 exact head b528fbcf672a9f25e99a75e1898b50bee639e22c.
- PR #92 exact-head Actions run 45019152380 passed on Ubuntu and hosted Windows. This verifies that PR #92 head only; each follow-up head requires its own CI evidence.
- PR #92's immutable in-memory payload closes the staged-file mutation gap but can consume substantial RAM. This follow-up adds a 256 MiB default size ceiling, a positive --max-upload-bytes override, and incremental copy-time enforcement so source growth is rejected before full payload capture.
- Keep the exact immutable bytes as the approved/uploaded payload. Do not replace this with a mutable path or file descriptor without a separately proven immutable mechanism.
- The default limit is not a device-specific guarantee. Before any real upload, the owner must choose a conservative limit based on the actual machine's available memory and expected clip sizes.
- Draft only; local tests and exact-head CI are pending. No credentials/tokens, real media, live OAuth, upload, public publishing, merge, retarget, deployment, or destructive action is part of this workstream.


### ARO-CHAT-0045 CI evidence refresh — 2026-11-22
- PR #93 implementation SHA `5cf8cc7e823f7ce9e8f319704d72c5f0da00d496` passed Actions run `45019724453`: Ubuntu and hosted Windows both passed setup, FFmpeg/FFprobe installation, compilation, full unittest step, and synthetic MP4/FFprobe validation.
- The connector exposed step conclusions but not test-log counts; do not infer a test count. Hosted Windows CI is not owner-device Windows verification.
- The subsequent registry-only documentation commit does not inherit the implementation SHA's exact-head CI claim. PR #93 remains draft/open/unmerged. Owner must review a device-appropriate upload memory budget before any real upload; no real media, live OAuth, upload, or public publishing was performed.


### ARO-CHAT-0046 exact-head CI reconciliation — 2026-11-22
- PR #93's documentation-only branch tip f9834d29235738573ad773f19ebcc9b7c0f4c129 has now been checked directly: Actions run 45020379946 succeeded on that exact commit.
- Ubuntu job 137201721141 and hosted Windows job 137201721314 passed setup, compilation, full unittest steps, and synthetic MP4/FFprobe validation. No numeric test count is asserted because test logs/counts were not returned in this audit.
- This supersedes the prior note that the documentation-only tip had no exact-head run. Hosted Windows CI is not owner-device verification, and synthetic media is not GTA 6 footage.
- PR #93 remains draft/open/unmerged. Before any real upload, the owner must choose a conservative --max-upload-bytes limit based on actual device RAM and expected clip sizes.
- Remaining gates: independent security review and owner-controlled resolution of Issue #68's parallel uploader PRs; creator-authorized GTA 6 media and permission evidence; local render, FFprobe validation, playback, and owner acceptance.


### Latest workstream refresh — ARO-CHAT-0048 (2026-11-22)
- Latest recorded bounded workstream: ARO-CHAT-0048 / ARO-GTA-P1-48, branch `workstream/aro-chat-0048-direct-upload-size-guard-test-2026-11-22`, PR #96. Its exact head `1ef93e7964afe13533fc25c0b9b6f0244462f343` passed Actions run `45055224315`; Ubuntu job `137308884581` and hosted Windows job `137308884348` passed compilation, complete unittest steps, and synthetic MP4/FFprobe validation. The PR record reports 332 tests passed per job; the connector step summary does not independently expose test-log counts. Hosted Windows CI is not owner-device verification; synthetic media is not GTA 6 footage.
- The ARO-CHAT-0048 change is test-only: direct oversized `upload_video()` calls must fail before OAuth authorization and must not create a token file. No network upload is performed. PR #96 remains draft/open/unmerged.
- The next pending project-level security gate remains Issue #68 (OPEN / WAITING_FOR_OWNER_APPROVAL). It requires the project owner to assign an implementation owner and explicitly select a canonical security PR/branch or approve a consolidation plan. Do not create competing uploader implementations or integrate/merge parallel PRs without that decision.
- Until Issue #68 is owner-approved and independently verified, keep public uploads disabled. No credentials/tokens, real media, live OAuth, live upload, public publishing, merge, retarget, or deployment are authorized by this follow-up.
