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


## LIVE REPOSITORY UPDATE — 2026-11-24 (ARO-CHAT-0193)

- Latest audited narrow security fix: draft PR #289, Chat ARO-CHAT-0132 / Workstream ARO-GTA-P1-132, head `4e01f16e97b2239c74a2f96c4262b04b57a4ae73`.
- Exact-head-associated Actions run #45386732186 succeeded. Ubuntu job #138419476509 and hosted-Windows job #138419476953 each compiled and ran the same 323-test suite successfully, then rendered and FFprobe-validated a synthetic MP4.
- Both jobs checked out PR #289's merge ref at `c1980d7c5aea879e86a17b1b8b51a7de101bfc28`, merging audited head into base `20427e0cad2e682076c627343e14b0f6f2f4f4a8`. Raw-head-only checkout is not demonstrated.
- Synthetic logs explicitly confirm no GTA 6 footage, no third-party media, publishing disabled, and manual review required. This is not real-media acceptance.
- PR #289 remains OPEN / DRAFT / UNMERGED. Independent review is not recorded; combined status has zero entries. Do not describe zero status entries as a passing combined status.
- Documentation-only audit: Chat ARO-CHAT-0193 / Workstream ARO-GTA-P1-193, branch `workstream/aro-chat-0193-pr289-exact-head-ci-audit-2026-11-24`, report `docs/ARO_CHAT_0193_PR289_CI_AUDIT.md`.
- Issue #68 remains OPEN and its authenticated owner-approval integration is not complete. The narrow PRIVATE-only guard fix does not authorize OAuth, live uploads, public publishing, merge, deployment, or real-media processing.
- No local tests were run in the audit session. No workflow retry was initiated.
- The repository's default branch currently exposes `docs/MASTER_PLAN.md`; a separate file named `MASTER_SCRIPT.md` was not found in the inspected root/docs paths. The canonical workstream registry and startup prompt are present on the PR #289 workstream branch, not on `main`. Always inspect the exact selected branch before assuming documentation is synchronized.


## LIVE REPOSITORY UPDATE — 2026-11-24 (ARO-CHAT-0194)

- Latest audit continuation: ARO-CHAT-0194 / ARO-GTA-P1-194, independently auditing PR #291's own exact-head CI.
- Audited PR #291 head: `c99e3027c196ea057001f5e785195b8a974dd5eb`; exact-head-associated run [#45387645247](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45387645247), run 1223, completed SUCCESS.
- Ubuntu job #138422673647 and hosted-Windows job #138422674151 each compiled, passed the same 323-test suite, and passed synthetic MP4/FFprobe validation.
- Both jobs checked out PR #291 merge ref `5a2a576bc2fb8f5daad2fba83c2a6f8c40a48dea`, merging audited head into base `4e01f16e97b2239c74a2f96c4262b04b57a4ae73`. Raw-head-only checkout is NOT DEMONSTRATED.
- Synthetic-only; no GTA 6/third-party media, publishing disabled, manual review required, mocked approval reports upload_performed=false. This is not real-media acceptance.
- PR #291 review submissions, inline threads, and conversation comments were empty; independent review NOT RECORDED. Combined status had zero entries, not a separate green context.
- Report: `docs/ARO_CHAT_0194_PR291_CI_AUDIT.md`. This follow-up is documentation-only; no workflow retry, OAuth, credentials, real media, upload, publishing, merge, retarget, deployment, or destructive action.
- Issue #68 remains OPEN. Keep live uploads/public publishing disabled pending independent security review, owner-controlled integration, owner-device verification, and authorized real-media acceptance.


## LIVE REPOSITORY UPDATE — 2026-11-24 (ARO-CHAT-0194 PR #294 CI closeout)

- Current audit workstream: ARO-CHAT-0194 / ARO-GTA-P1-194; audit PR #294 head `b048589231975e20839654e6fdff46eab34539ca`; branch `workstream/aro-chat-0194-pr291-exact-head-ci-audit-2026-11-24`.
- PR #294's own Actions run [#45388055676](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45388055676), run 1228, completed SUCCESS.
- Ubuntu job #138424089845 and hosted-Windows job #138424090425 each passed compilation and the same 323-test suite (4.261s Ubuntu; 13.725s Windows), then passed synthetic MP4/FFprobe validation.
- Both jobs checked out PR #294 merge ref `e30fd38ce8a224a3def3cfa989fcd00c6083641d`, merging audited head into base `c99e3027c196ea057001f5e785195b8a974dd5eb`. Raw-head-only checkout NOT DEMONSTRATED.
- Synthetic media only; no GTA 6 or third-party footage, publishing disabled, manual review required, mocked approval reports `upload_performed=false`. Same 323 tests ran on both platforms, not 646 unique tests.
- PR #294 review submissions, inline threads, and conversation comments were empty; independent review NOT RECORDED. PR remains OPEN / DRAFT / UNMERGED.
- Report: `docs/ARO_CHAT_0194_PR294_CI_AUDIT.md`. Do not transfer this run to another PR or SHA. Owner-device Windows and authorized real-media acceptance remain NOT VERIFIED.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled. No OAuth, credentials, real media, network upload, publishing, workflow retry, merge, rebase, retarget, deployment, or destructive action was performed.
