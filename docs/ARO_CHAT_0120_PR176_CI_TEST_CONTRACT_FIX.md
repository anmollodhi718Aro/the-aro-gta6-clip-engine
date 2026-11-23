# ARO-CHAT-0120 | PR #176 CI Test-Contract Fix

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0120
- Exact title: ARO-CHAT-0120 | PR #176 CI Test-Contract Fix
- Workstream ID: ARO-GTA-P1-120
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0120-pr176-ci-test-contract-fix-2026-11-24`
- Base / starting SHA: PR #176 head `2a83ce65706d0a8ccce0d5eaf56651fb9f5caa69`
- Parent PR: #176

## Finding
PR #176 exact-head run #45253188457 failed on both Ubuntu and hosted Windows in the same test. The regression tried to chmod/write `approved-upload.mp4` during the upload request, but the implementation now captures the approved bytes in memory and removes the temporary staging directory before OAuth/API activity. The test expected a temp file that should no longer exist.

## Change
- Reframed the test as `test_temporary_staging_is_cleaned_before_upload_and_payload_remains_immutable`.
- Assert the temporary staging directory and file are absent when the upload request is constructed.
- Mutate the original source after staging and final checks.
- Assert the upload stream still contains the exact bytes captured before OAuth and is not affected by the later source mutation.
- No production uploader behavior changed.

## Verification
- Local tests: NOT RUN in this connector session.
- This branch's exact-head CI: PENDING; inspect its own Ubuntu and hosted-Windows logs before claiming TESTED or CI_VERIFIED.
- PR #176 run #45253188457 is failure evidence for the parent branch only; it is not a result for this follow-up.
- No live OAuth, credentials/tokens, real media, network upload, or publishing was used.

## Safety and remaining gates
- Draft follow-up only; no merge, retarget, deployment, upload, or public publishing.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live/public uploads disabled pending owner assignment, independent security review, and owner-controlled integration.
- The owner must choose a device-appropriate `--max-upload-bytes` before any real upload.
- Hosted Windows CI is not owner-device verification; synthetic media is not real GTA 6 media acceptance.
