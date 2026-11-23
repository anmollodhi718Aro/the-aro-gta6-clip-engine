

## ARO-CHAT-0147 PR #220 exact-head CI closeout — 2026-11-24

- Workstream: ARO-GTA-P1-147; branch `workstream/aro-chat-0147-pr220-exact-head-ci-audit-2026-11-24`; parent audited: PR #220 head `47072a6ac9b42d48d273176dc7e04fe019779fd7`.
- PR #220 CI run [#45269033752](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45269033752), run 1061, completed SUCCESS. Ubuntu job #138023584264 and hosted-Windows job #138023585270 both passed compilation, the same 338-test suite, and synthetic MP4/FFprobe validation.
- Both jobs checked out `refs/remotes/pull/220/merge` at merge SHA `9af7af7864be8ad950f2df49e9fa811c2073e824`, merging PR #220 head into base `cdacb24c9d1db25ad0a85f93d51afabb94d6f836`. Raw-head-only checkout is NOT DEMONSTRATED. Do not count the two platform runs as 676 unique tests.
- Synthetic fixture only; no GTA 6 or third-party footage. Publishing disabled, manual review required, mocked upload reports `upload_performed=false`. Combined status had zero entries; reviews and inline threads empty; independent review NOT RECORDED.
- PR #220 audit is CI_VERIFIED on merge ref only. Hosted Windows is not owner-device verification; synthetic media is not real-media acceptance. Local tests NOT RUN; no workflow retry.
- This documentation closeout is committed in the existing ARO-CHAT-0147 branch / PR #221. PR #221's own exact-head CI remains separately PENDING verification; do not transfer PR #220 evidence.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL / UNASSIGNED. Keep live uploads/public publishing disabled. No OAuth, credentials, real media, network upload, publishing, merge, rebase, retarget, deployment, or destructive action.


### PR #221 follow-up CI evidence and current-head limitation — 2026-11-24
- PR #221 initial head `eee181efc37f040b77e91df416a77983d7c7c687` completed Python CI run [#45269230348](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45269230348), run 1062, SUCCESS.
- Ubuntu job #138024276868 passed compilation, 338 tests (4.303s), and synthetic MP4/FFprobe validation. Hosted-Windows job #138024276330 passed compilation, the same 338 tests (15.093s), and synthetic MP4/FFprobe validation.
- Both jobs checked out `refs/remotes/pull/221/merge` at merge SHA `cba11074982e05c4c5c725c5292223a9a129cf6c`, merging PR #221 initial head into base/PR #220 head `47072a6ac9b42d48d273176dc7e04fe019779fd7`. Raw-head-only checkout is NOT DEMONSTRATED; the platforms ran the same 338-test suite, not 676 unique tests.
- Synthetic reports used locally generated pattern/tone only, no GTA 6 or third-party media, publishing disabled, manual review required, and mocked upload `upload_performed=false`.
- After the audit documentation commits, PR #221 head `0d215e8c868f0df5be5e04026845afc4b1ea6f77` had zero associated workflow runs and zero combined status entries. That latest head is PENDING / NOT CI_VERIFIED; run #45269230348 does not transfer. PR #221 remained OPEN / DRAFT / UNMERGED, GitHub reported mergeable=false, and reviews, inline threads, and conversation comments were empty. Local tests NOT RUN.
- PR #220 audit remains CI_VERIFIED on merge ref only. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL / UNASSIGNED; keep live uploads/public publishing disabled. No workflow retry, merge, rebase, retarget, deployment, upload, publishing, credentials, OAuth, or destructive action was performed.
