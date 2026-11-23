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
