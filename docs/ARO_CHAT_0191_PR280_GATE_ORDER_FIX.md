# ARO-CHAT-0191 | Fix PRIVATE upload gate ordering

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0191
- Exact chat title: ARO-CHAT-0191 | Fix PR #280 PRIVATE Gate Ordering
- Workstream ID: ARO-GTA-P1-191
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: workstream/aro-chat-0191-pr280-private-gate-order-2026-11-24
- Base / starting SHA: PR #280 head 20427e0cad2e682076c627343e14b0f6f2f4f4a8

## Finding
PR #280's exact-head Actions run #45385315409 (run 1212) failed on both Ubuntu and hosted Windows. Compilation passed, but each platform's full 323-test suite failed with one error in `test_upload_rejects_unlisted_visibility_before_oauth_or_api`.

The traceback showed `upload_video()` importing `googleapiclient.discovery` before checking the requested privacy. Because the optional `[youtube-upload]` extra is not installed in the default CI environment, the import raised `ModuleNotFoundError`, which was converted to a `RuntimeError`. The expected fail-closed PRIVATE-only `PermissionError` was never reached. The synthetic MP4/FFprobe step was skipped after the test failure.

## Change
- Move the explicit operator-confirmation and PRIVATE-only intent checks to the beginning of `upload_video()`, before optional YouTube client imports and before OAuth/API setup.
- Strengthen the regression test so it fails if `googleapiclient` is imported while rejecting an unlisted request.
- Preserve all existing OAuth identity, per-clip approval, rights rechecks, and actual upload behavior for the separately gated PRIVATE path.

## Validation evidence
- Parent PR #280 head: `20427e0cad2e682076c627343e14b0f6f2f4f4a8`.
- Parent run #45385315409 (run 1212): FAILED on Ubuntu job #138414594021 and hosted-Windows job #138414593509.
- Both jobs checked out `refs/remotes/pull/280/merge` at merge SHA `86b4481ab61eddac2556bf3b6364d23594c67771`, merging the audited head into base `f66f6406a496d08e3e85972010f1f52d831298ab`.
- Both platforms ran 323 tests; the same single test errored. Durations: 4.971s Ubuntu and 13.080s Windows.
- The failure was dependency-import ordering, not an upload attempt. No network upload occurred. Synthetic rendering was skipped because the test step failed.
- Local tests in this connector session: NOT RUN. This follow-up branch's exact-head CI: PENDING until its own run is inspected.

## Safety
- Narrow fail-closed ordering fix and regression test only.
- No OAuth login, credentials, network upload, real media, publishing, merge, rebase, retarget, deployment, workflow retry, or destructive action.
- PR #280 remains OPEN / DRAFT / UNMERGED; this follow-up does not authorize integration or upload.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled pending owner-controlled canonical integration, independent security review, authenticated channel-owner binding, exact per-clip approval, current rights checks, and owner acceptance.
