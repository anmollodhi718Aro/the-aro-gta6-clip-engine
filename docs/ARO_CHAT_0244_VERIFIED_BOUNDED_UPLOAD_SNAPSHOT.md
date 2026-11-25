# ARO-CHAT-0244 — Verified bounded upload source snapshot

Date: 2026-11-25  
Repository: anmollodhi718Aro/the-aro-gta6-clip-engine  
Branch: workstream/aro-chat-0244-verified-bounded-upload-snapshot-2026-11-25  
Parent: PR #378

## Objective

Close the gap between the bounded temporary snapshot in PR #378 and the stronger descriptor/path identity checks previously present on PR #328. The uploader must not silently approve one source and transfer bytes from a replaced or modified source.

## Implementation

- Validate a positive owner-selected upload byte limit.
- Use lstat to reject symlinks and non-regular files before opening.
- Open the source with O_NOFOLLOW and O_NONBLOCK where supported.
- Compare pre-open path device/inode with the opened descriptor.
- Copy from the opened descriptor in 1 MiB chunks into an exclusive temporary file, rejecting growth beyond the configured limit.
- Compare descriptor device, inode, size, modification time and change time before/after copying.
- Recheck the source pathname after copying and reject replacement or non-regular substitutions.
- Pass the same bounded snapshot to the existing approval hash and resumable upload path; clean it up in a finally block.

## Regression coverage

- Reject symlink source paths.
- Reject FIFO/special-file sources without blocking.
- Reject in-place source mutation during snapshot creation, including same-size replacement with restored modification time.
- Preserve existing bounded-size, snapshot-byte identity and cleanup tests.

## Validation status

- Source commit: c6a0569d1093e7857958767c447a499e019109da
- Test commit: e095bcb51364558f04fb7ce1be74f945b3891a67
- Local repository tests: NOT RUN in this connector session.
- Exact-head Ubuntu and hosted-Windows CI: PENDING.
- Parent PR #378's latest observed run #45612283558 failed with both jobs exposing no steps and no log URLs. This is not a compile/test result; failure phase and cause are UNVERIFIED and are not attributed to application code.

## Safety

Draft-only code change. No OAuth, credentials, real media, upload, public publishing, merge, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled. Independent security review, owner-device OAuth/channel verification, owner-selected upload limit, and authorized real-media PRIVATE acceptance remain separate gates.



### Exact-head CI recheck — 2026-11-25
- PR #385 head `b8704221f4ba3131d8c6b96e2d091a9530eea5b2` is associated with run #45657905605, conclusion FAILURE.
- Ubuntu job #139359465979 and hosted-Windows job #139359466345 both expose `steps: null` and `logs_url: null`. No compile/test result is available; failure phase and cause remain UNVERIFIED and are not attributed to application code.
- Do not blindly rerun or dispatch workflows. Exact-head CI remains NOT VERIFIED; local repository tests NOT RUN.
