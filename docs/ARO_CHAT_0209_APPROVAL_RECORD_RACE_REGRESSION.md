# ARO-CHAT-0209 | Restore approval-record open-race protection

Date: 2026-11-24

## Finding
The consolidated private-upload branch PR #311 was based on PR #295 and did not carry forward the approval-record path hardening from PR #305. Its `require_current_owner_approval()` used `Path.read_text()` directly, so the reader no longer rejected symlink/non-regular paths or bound the opened descriptor to the pre-open file identity.

This is a regression in the consolidated integration line, not a finding that PR #305's own branch lacked the fix.

## Change
- Restore pre-open symlink and regular-file checks with `is_symlink()` and `lstat()`.
- Open with `O_NOFOLLOW` and `O_NONBLOCK` where supported.
- Compare `(st_dev, st_ino)` from pre-open `lstat()` with `fstat()` on the opened descriptor; reject a replaced path.
- Ensure descriptors are closed on every error path.
- Restore regression tests for pre-existing symlink, regular-file replacement, directory path, FIFO path, and FIFO replacement between check and open. FIFO/symlink tests skip only where the platform cannot create those filesystem objects.

## Workstream
- Chat ID: ARO-CHAT-0209
- Exact title: ARO-CHAT-0209 | Restore Approval-Record Open-Race Protection in Consolidated Uploader
- Workstream ID: ARO-GTA-P1-209
- Branch: `workstream/aro-chat-0209-restore-approval-record-open-race-2026-11-24`
- Base / starting SHA: PR #311 head `c3d767fd055c80dbd395c5c8821a335ad9b3b258`
- Parent PR: #311
- Code commit: `72f72e26c2a58ce01066275f56b4c4f649ed6bf2`
- Test commit: `da3d774a14565b3d3bc99d61b8335e92aaf96cff`

## Validation
- Local tests: NOT RUN in this connector session.
- Exact-head GitHub Actions: PENDING; no pass is claimed.
- Owner-device Windows verification: NOT VERIFIED.
- Real GTA 6 media: NOT USED; real-media acceptance NOT VERIFIED.
- No OAuth, credentials/tokens, network upload, publishing, merge, rebase, retarget, deployment, or destructive action.

## Safety
PR #311 remains OPEN / DRAFT / UNMERGED. This follow-up is draft-only and stacked on its exact current head. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled until the complete security review, owner-controlled integration, owner-device verification, and separately authorized real-media PRIVATE acceptance are completed.

## CI closeout — 2026-11-24

- PR #317 current code head `8e9bd5ef546c28b2cb2633e7e99373725b1fc053` was associated with Actions run [#45422909011](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45422909011), run 1338; run conclusion SUCCESS.
- Ubuntu job passed compilation, 342 unit tests (`Ran 342 tests in 3.582s`), and synthetic MP4/FFprobe validation.
- Hosted-Windows job passed compilation, 342 unit tests (`Ran 342 tests in 16.748s`, `OK (skipped=2)`), and synthetic MP4/FFprobe validation.
- Both jobs checked out `refs/remotes/pull/317/merge`; this is successful PR merge-ref CI, not evidence of raw-head-only checkout. The same 342-test suite ran on each platform, not 684 unique tests.
- Logs confirm locally generated synthetic pattern/tone only, `gta6_footage_used=false`, `third_party_media_used=false`, `upload_performed=false`, `publishing_enabled=false`, and `manual_review_required=true`.
- PR #317 review submissions, inline review threads, and conversation comments: none recorded; independent review NOT RECORDED. Local tests NOT RUN in this connector session.
- Hosted Windows is not owner-device verification. Real-media acceptance remains NOT VERIFIED. PR #317 remains OPEN / DRAFT / UNMERGED; Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
