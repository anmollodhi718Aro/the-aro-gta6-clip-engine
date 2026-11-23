# ARO-CHAT-0111 | PR #176 Immutable-Payload Regression Repair

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0111
- Exact chat title: ARO-CHAT-0111 | PR #176 Immutable-Payload Regression Repair
- Workstream ID: ARO-GTA-P1-111
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0111-pr176-staging-test-fix-2026-11-24`
- Base / starting SHA: PR #176 head `2a83ce65706d0a8ccce0d5eaf56651fb9f5caa69`
- Parent PR: #176
- Scope: repair one regression test whose filesystem mutation target became invalid after the implementation correctly moved immutable byte capture and staging cleanup before OAuth.

## Failure evidence
- Parent PR #176 head `2a83ce65706d0a8ccce0d5eaf56651fb9f5caa69` was associated with Python CI run #45253188457 (run 998), conclusion FAILURE.
- Ubuntu job #137968068714 and hosted-Windows job #137968069252 both compiled successfully, then failed in the unit-test step.
- Both platforms failed only at `test_staged_file_mutation_after_final_checks_cannot_change_upload_payload`.
- The test attempted to chmod/write `approved-upload.mp4` from a temporary staging directory after `upload_video()` had already exited that directory and captured the exact payload into immutable in-memory bytes. The observed failure was FileNotFoundError on both platforms.
- Each platform ran 338 tests; the same single test errored. Synthetic MP4/FFprobe steps were skipped because the unit-test step failed.

## Change
- Rename the test to `test_source_file_mutation_after_final_checks_cannot_change_upload_payload`.
- Remove the stale temporary-directory recorder and staging-path mutation.
- Mutate the original source file at the mocked upload-request boundary, after final approval/rights checks.
- Assert the upload stream still contains the previously approved bytes and differs from the now-mutated source.
- No uploader production code or approval logic changed.

## Verification
- The test-only correction is committed; local tests were not run in this connector session.
- This branch's exact-head Ubuntu/hosted-Windows CI is pending and must be inspected independently.
- Do not transfer PR #176's failed run or any predecessor CI result as verification of this branch.

## Safety and owner gates
- PR #176 and this follow-up remain draft/unmerged. No merge, retarget, deployment, OAuth, credentials/tokens, real media, network upload, public publishing, or destructive action was performed.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled pending owner assignment, independent security review, owner-controlled integration, and device-appropriate upload-limit selection.
- Hosted Windows CI is not owner-device verification; synthetic media is not real GTA 6 media acceptance.
