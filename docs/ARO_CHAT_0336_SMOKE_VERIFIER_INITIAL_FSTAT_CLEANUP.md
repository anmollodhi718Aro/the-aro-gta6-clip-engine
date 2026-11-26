# ARO-CHAT-0336 | Close smoke verifier descriptor when initial fstat fails

- Chat ID: ARO-CHAT-0336
- Workstream: ARO-GTA-P0-336
- Scope: one focused regression test on the existing P0 draft PR #386 branch and original base.
- Added a test that injects an `OSError` from the verifier's first `os.fstat()` after `os.open()` succeeds. It verifies the descriptor is closed by the helper's `finally` block.
- Production code unchanged. This complements the existing read-failure descriptor-cleanup regression by covering the earlier metadata-inspection failure point.
- Test commit: `4505d5678ce3c46bd128aa4ab2aa6836247e40f2`.
- Tests NOT RUN in this connector session. Synthetic FFmpeg end-to-end NOT RUN. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED. Independent review NOT RECORDED. Owner-device Windows verification NOT VERIFIED. Authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and original branch/base. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
