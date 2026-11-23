# ARO-CHAT-0147 | PR #220 Exact-Head CI Audit

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0147
- Exact chat title: ARO-CHAT-0147 | PR #220 Exact-Head CI Audit
- Workstream ID: ARO-GTA-P1-147
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Role: Documentation-only exact-head CI auditor
- Branch: `workstream/aro-chat-0147-pr220-exact-head-ci-audit-2026-11-24`
- Base / starting SHA: PR #220 head `47072a6ac9b42d48d273176dc7e04fe019779fd7`
- Parent PR: [#220](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/220)

## Task and scope
Independently inspect PR #220's own commit-associated GitHub Actions run, jobs/logs, checkout refs, compilation/tests, synthetic MP4/FFprobe validation, combined status, and review state. Record observed evidence only. Documentation-only; no application, uploader, test, renderer, media-ingestion, or workflow behavior changes.

## Exact-head CI evidence
- PR #220 head: `47072a6ac9b42d48d273176dc7e04fe019779fd7`.
- Commit-associated Python CI run [#45269033752](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45269033752), run 1061, completed SUCCESS.
- Ubuntu job #138023584264 completed successfully: source compilation passed; the complete unittest suite ran 338 tests in 5.142s and returned OK; synthetic MP4/FFprobe validation passed.
- Hosted-Windows job #138023585270 completed successfully: source compilation passed; the complete unittest suite ran the same 338 tests in 15.764s and returned OK; synthetic MP4/FFprobe validation passed.
- Both jobs checked out `refs/remotes/pull/220/merge` at merge SHA `9af7af7864be8ad950f2df49e9fa811c2073e824`, merging PR #220 head `47072a6ac9b42d48d273176dc7e04fe019779fd7` into base `cdacb24c9d1db25ad0a85f93d51afabb94d6f836` (PR #219 head). Raw-head-only checkout is NOT DEMONSTRATED.
- Both platforms ran the same 338-test suite, not 676 unique tests.
- Both synthetic reports show locally generated test pattern/tone only, 8.0-second source, 4.0-second rendered output, `gta6_footage_used=false`, `third_party_media_used=false`, `publishing_enabled=false`, and `manual_review_required=true`. Mocked upload evidence reports `upload_performed=false`. No real GTA 6 or third-party media was used; no live upload or publishing was performed.
- Non-failing Node.js 20 deprecation warnings were emitted for actions/checkout@v4 and actions/setup-python@v5.
- Combined commit status returned zero status entries. The successful commit-associated Actions run and completed job logs are the CI evidence; an empty combined-status list is not itself a passing check.

## Review and status
- PR #220 review submissions, inline review threads, and conversation comments returned empty arrays. Independent review is NOT RECORDED.
- PR #220 remains OPEN / DRAFT / UNMERGED; GitHub reported mergeable=true at inspection.
- Audit result: CI_VERIFIED on the PR merge ref only. Raw-head-only CI is NOT DEMONSTRATED. Hosted Windows CI is not owner-device verification.
- Local tests were NOT RUN in this connector session.
- PR #221's initial head `eee181efc37f040b77e91df416a77983d7c7c687` completed its own Python CI run [#45269230348](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45269230348), run 1062, SUCCESS. Ubuntu job #138024276868 passed compilation, 338 tests (4.303s), and synthetic MP4/FFprobe validation; hosted-Windows job #138024276330 passed compilation, the same 338 tests (15.093s), and synthetic MP4/FFprobe validation. Both checked out `refs/remotes/pull/221/merge` at merge SHA `cba11074982e05c4c5c725c5292223a9a129cf6c`, merging that PR #221 head into base/PR #220 head `47072a6ac9b42d48d273176dc7e04fe019779fd7`. Raw-head-only checkout is NOT DEMONSTRATED; this is not 676 unique tests. Synthetic-only media, no GTA 6/third-party media, publishing disabled, manual review required; mocked upload `upload_performed=false`.
- After three documentation commits updated PR #221, its then-current head `0d215e8c868f0df5be5e04026845afc4b1ea6f77` had zero commit-associated workflow runs and zero combined status entries. Therefore PR #221's latest documentation head is PENDING / NOT CI_VERIFIED; run #45269230348 does not transfer to it. PR #221 remained OPEN / DRAFT / UNMERGED, GitHub reported mergeable=false, and its reviews, inline threads, and conversation comments were empty. No local tests were run.

## Safety and limitations
- Documentation-only; no application/uploader/test/renderer/media-ingestion/workflow behavior changes.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL / UNASSIGNED. Keep live uploads/public publishing disabled.
- Synthetic media is not real GTA 6 footage or real-media acceptance. Hosted Windows is not owner-device verification.
- No credentials/tokens, OAuth, real media, network upload, public publishing, workflow retry, merge, rebase, retarget, deployment, or destructive action was performed.


## Final exact-head CI closeout — 2026-11-24 02:54 IST

- PR #220 head `47072a6ac9b42d48d273176dc7e04fe019779fd7` is associated with Python CI run [#45269033752](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45269033752), run 1061; workflow conclusion SUCCESS.
- Ubuntu job #138023584264 completed SUCCESS. Its log confirms checkout of `refs/remotes/pull/220/merge` at merge SHA `9af7af7864be8ad950f2df49e9fa811c2073e824`, merging audited PR #220 head into base `cdacb24c9d1db25ad0a85f93d51afabb94d6f836`. Python 3.11 compilation passed; 338 unit tests passed (5.142s); synthetic MP4/FFprobe validation passed.
- Hosted-Windows job #138023585270 completed SUCCESS. Its log confirms the same PR merge ref and merge SHA. Python 3.11 compilation passed; 338 unit tests passed (15.764s); synthetic MP4/FFprobe validation passed.
- Both platform runs execute the same 338-test suite, not 676 unique tests. The synthetic reports identify locally generated test pattern/tone, `gta6_footage_used=false`, `third_party_media_used=false`, `publishing_enabled=false`, and `manual_review_required=true`. Mock upload fixture reports `upload_performed=false`.
- Combined commit status returned zero status entries; this is not a passing status signal. The successful commit-associated Actions run and both successful job conclusions are the CI evidence.
- PR #220 review submissions and inline review threads returned empty arrays. Independent review NOT RECORDED. Conversation comments were empty at initial inspection.
- Audit conclusion: CI_VERIFIED on the PR merge ref only. Raw-head-only checkout is NOT DEMONSTRATED. Hosted Windows is not owner-device verification; synthetic media is not real-media acceptance.
- Local tests NOT RUN in this connector session. No workflow retry initiated. No credentials/tokens, OAuth session, real media, network upload, public publishing, merge, rebase, retarget, deployment, or destructive action performed.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL / UNASSIGNED. Keep live uploads/public publishing disabled.
- This workstream's own PR #221 exact-head CI must be inspected independently; PR #220's successful CI does not transfer to PR #221.


## PR #221 follow-up CI and current-head status
- Initial PR #221 head `eee181efc37f040b77e91df416a77983d7c7c687` completed run [#45269230348](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45269230348), run 1062, SUCCESS. Ubuntu job #138024276868 passed compilation, 338 tests (4.303s), and synthetic MP4/FFprobe; hosted-Windows job #138024276330 passed compilation, the same 338 tests (15.093s), and synthetic MP4/FFprobe.
- Both jobs checked out `refs/remotes/pull/221/merge` at merge SHA `cba11074982e05c4c5c725c5292223a9a129cf6c`, merging that initial PR #221 head into base/PR #220 head `47072a6ac9b42d48d273176dc7e04fe019779fd7`. Raw-head-only checkout is NOT DEMONSTRATED; the platforms ran the same 338-test suite, not 676 unique tests. Synthetic media was locally generated only; no GTA 6/third-party media, publishing disabled, manual review required, mocked upload `upload_performed=false`.
- After documentation commits, latest observed PR #221 head `0d215e8c868f0df5be5e04026845afc4b1ea6f77` had zero associated workflow runs and zero combined status entries. That latest head is PENDING / NOT CI_VERIFIED; the earlier run does not transfer. PR #221 remained OPEN / DRAFT / UNMERGED, mergeable=false, with no reviews, inline threads, or conversation comments. Local tests NOT RUN.
