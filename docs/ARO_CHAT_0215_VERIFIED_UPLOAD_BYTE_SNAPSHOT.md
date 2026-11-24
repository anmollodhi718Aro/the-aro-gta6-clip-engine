# ARO-CHAT-0215 | Bind YouTube upload bytes to the approved snapshot

Date: 2026-11-24

## Finding

The approval record binds consent to a SHA-256 hash of the selected video. The YouTube resumable media helper reads from a filename during transfer, so continuing to pass the original mutable source path leaves a time-of-check/time-of-use gap between the final approval hash check and the bytes read by the upload client.

## Change

- Open the selected source as a regular file, using no-follow and nonblocking semantics where supported; this also rejects a raced FIFO without hanging.
- Compare the pre-open path identity with the opened descriptor.
- Copy bytes from that same descriptor into a private temporary staging directory while calculating the snapshot hash.
- Re-check descriptor metadata and the current source pathname after copying; fail closed if identity, size, modification metadata, or file type changed during the snapshot.
- Make the snapshot read-only and use that exact snapshot path for both durable approval-hash verification and the MediaFileUpload body.
- Clean up the temporary snapshot after the upload attempt, including failure paths.
- Add a regression test that changes the original source immediately before the mocked YouTube insert and verifies the media body still references the original approved bytes.
- Add a platform-aware regression test proving a raced FIFO source is rejected without blocking.

## Workstream

- Chat ID: ARO-CHAT-0215
- Workstream ID: ARO-GTA-P1-215
- Branch: workstream/aro-chat-0215-verified-upload-byte-snapshot-2026-11-24
- Base / starting SHA: PR #311 head 67e6d4290fee795fb8ba6fd0e926107ea7f0eb81
- Parent: draft PR #311
- Code commits: 1fefe87ef47dd4be723cab8ba9424b31156e46c1 and f14f00758fad5cd400f4a1efeacb9e04256a279d
- Regression test commit: 7d8fd5c85f4171e702cada1d0e6c9fcece2a494b
- Report: docs/ARO_CHAT_0215_VERIFIED_UPLOAD_BYTE_SNAPSHOT.md

## Validation

- Local tests in this connector session: NOT RUN.
- Initial exact-head CI for the pre-FIFO-follow-up head passed on Ubuntu and hosted Windows: run #45426822957, 341 tests on each platform and synthetic MP4/FFprobe validation. The subsequent FIFO-hardening commits require fresh exact-head CI, currently PENDING.
- No OAuth credentials, real media, network upload, merge, deployment, or publishing used.
- Owner-device verification and real-media PRIVATE acceptance: NOT VERIFIED.

## Safety

Draft-only follow-up. PR #311 and its dependency chain remain unmerged. Issue #68 remains open pending complete independent review and owner-controlled acceptance. Public publishing remains disabled.

## Combined branch CI closeout — 2026-11-24
- PR #328 head `e1dd08c12d81e3a5c56eef65784955f0e55d4021` passed run #45428060156 on merge ref `b4adb085f8976e79bb70356b4314dbd450b23416` (PR head merged into base `67e6d4290fee795fb8ba6fd0e926107ea7f0eb81`).
- Ubuntu: compile passed, 348 tests passed, synthetic MP4/FFprobe passed.
- Hosted Windows: compile passed, 348 tests executed, 345 passed and 3 FIFO-only tests skipped because `os.mkfifo` is unavailable; synthetic MP4/FFprobe passed.
- Both platforms ran the same 348-test suite, not 696 unique tests. Raw-head-only checkout NOT DEMONSTRATED.
- The original-source mutation regression and same-inode approval-record symlink regression passed on both platforms. The FIFO race regression passed on Ubuntu; the three FIFO tests were skipped on Windows due to platform capability.
- Synthetic logs confirm no GTA 6 footage or third-party media, `upload_performed=false`, `publishing_enabled=false`, and `manual_review_required=true`. No OAuth or network upload.
- PR #328 review submissions remain empty; independent review NOT RECORDED. Owner-device and real-media PRIVATE acceptance NOT VERIFIED.
