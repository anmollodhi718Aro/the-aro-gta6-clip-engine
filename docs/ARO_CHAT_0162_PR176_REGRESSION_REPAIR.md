# ARO-CHAT-0162 | PR #176 Staged-Payload Mutation Regression Repair

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0162
- Exact title: ARO-CHAT-0162 | PR #176 Staged-Payload Mutation Regression Repair
- Workstream ID: ARO-GTA-P1-162
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0162-pr176-mutation-test-fix-2026-11-24`
- Base / starting SHA: PR #176 head `2a83ce65706d0a8ccce0d5eaf56651fb9f5caa69`
- Parent PR: #176 (stacked on #168)

## Review finding
The current PR #176 branch has a failing regression test on both Ubuntu and hosted Windows:
- PR #176 run #45253188457: Ubuntu job #137968068714 and Windows job #137968069252 failed during the unit-test step.
- PR #168 run #45257591368: Ubuntu job #137983367357 and Windows job #137983366907 failed on the same test.
- Failure: `test_staged_file_mutation_after_final_checks_cannot_change_upload_payload` raised `FileNotFoundError` for `approved-upload.mp4` inside the temporary staging directory.
- PR #176 intentionally captures the staged bytes into an immutable in-memory payload and exits the temporary-directory context before OAuth. Therefore, the old test's attempt to reopen and mutate the already-deleted staging file is inconsistent with the new implementation lifecycle.

## Change
- Rename the test to `test_source_file_mutation_after_final_checks_cannot_change_upload_payload`.
- Mutate the original source path from the mocked upload-insert boundary, after final approval/hash and rights checks have passed.
- Assert that the API client's media stream still contains the original approved bytes while the source path contains the changed bytes.
- Keep production uploader behavior unchanged. This is a regression-test correction, not a weakening of the immutable-payload guarantee.

## Validation
- Static diff review: the test now exercises the invariant that matters after pre-OAuth staging: later source-path mutation cannot change the already-captured upload payload.
- Local tests: NOT RUN in this connector session.
- This branch's exact-head Ubuntu and hosted-Windows CI: PENDING; do not transfer parent PR #168/#176 results.
- Required follow-up: inspect both job logs, test count, synthetic MP4/FFprobe and checkout refs for this branch's own head.

## Safety and remaining gates
- Draft follow-up only; no merge, retarget, deployment, OAuth, credentials/tokens, real media, network upload, or publishing.
- Issue #68 remains OPEN. Keep live/public uploads disabled until the canonical security lineage passes exact-head CI, independent review, owner-controlled integration, and the owner selects a device-appropriate `--max-upload-bytes`.
- No real GTA 6 media acceptance is claimed. Hosted Windows CI is not owner-device verification.


## Exact-head CI closeout — 2026-11-24

The test-fix commit `2a35e73351880d255177599cdbd2631741748033` was included in PR head `e2620b00c1ff383cc3b0d76be7da614d1ad5556a` and passed Python CI run [#45277330824](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45277330824), run 1101.

- Ubuntu job #138052406607: compilation passed; 338 tests passed in 4.902s; synthetic MP4/FFprobe passed.
- Hosted-Windows job #138052406300: compilation passed; the same 338 tests passed in 15.648s; synthetic MP4/FFprobe passed.
- Both jobs checked out `refs/remotes/pull/238/merge` at merge SHA `829d1fe11bc27456143f0119de4e4db734679f63`, merging PR head `e2620b00c1ff383cc3b0d76be7da614d1ad5556a` into base `2a83ce65706d0a8ccce0d5eaf56651fb9f5caa69`. Raw-head-only CI is NOT DEMONSTRATED.
- The corrected mutation regression passed on both platforms. Synthetic evidence reports `gta6_footage_used=false`, `third_party_media_used=false`, `publishing_enabled=false`, `manual_review_required=true`, and mocked `upload_performed=false`.
- This is 338 shared test cases run on two platforms, not 676 unique tests.
- Status for the tested code head: CI_VERIFIED on the PR merge ref. Owner-device Windows and authorized real-media acceptance remain NOT VERIFIED.


## Exact-head CI closeout — 2026-11-24
- Re-fetched PR #238: OPEN / DRAFT / UNMERGED; exact head remains `e2620b00c1ff383cc3b0d76be7da614d1ad5556a`, base is PR #176 head `2a83ce65706d0a8ccce0d5eaf56651fb9f5caa69`.
- This branch's own Python CI run [#45277330824](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45277330824), run 1101, completed SUCCESS.
- Ubuntu job #138052406607 completed SUCCESS: compilation passed; 338 tests passed (4.902s); synthetic MP4/FFprobe passed.
- Hosted-Windows job #138052406300 completed SUCCESS: compilation passed; the same 338 tests passed (15.648s); synthetic MP4/FFprobe passed. This is 338 shared test cases run on both platforms, not 676 unique tests.
- Both jobs checked out `refs/remotes/pull/238/merge` at merge SHA `829d1fe11bc27456143f0119de4e4db734679f63`, merging PR #238 head `e2620b00c1ff383cc3b0d76be7da614d1ad5556a` into base `2a83ce65706d0a8ccce0d5eaf56651fb9f5caa69`. Raw-head-only CI is NOT DEMONSTRATED.
- Synthetic test used locally generated pattern/tone only: 8.0-second source, 4.0-second output, `gta6_footage_used=false`, `third_party_media_used=false`, `publishing_enabled=false`, `manual_review_required=true`; mocked upload reports `upload_performed=false`.
- PR #238 combined commit status returned zero entries; this is not a separate passing status check. Reviews, inline review comments, and conversation comments were empty; independent review NOT RECORDED.
- Static diff inspection confirms only `tests/test_youtube_upload.py` plus audit/registry/startup documentation changed; `backend/app/youtube_upload.py` is unchanged. The corrected test mutates the original source at the mocked insert boundary and asserts the in-memory media stream still carries the originally approved bytes.
- Disposition: PR #238 merge-ref CI_VERIFIED (Ubuntu + hosted Windows); raw-head-only CI NOT DEMONSTRATED; local tests NOT RUN in this connector session; owner-device Windows and authorized real-media acceptance NOT VERIFIED.
- Keep PR #238 draft/open/unmerged pending independent security review and owner-controlled integration. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live/public uploads disabled. Owner-selected device-appropriate `--max-upload-bytes` remains required before any real upload. No OAuth, credentials/tokens, real media, network upload, publishing, merge, rebase, retarget, deployment, or destructive action was performed.
