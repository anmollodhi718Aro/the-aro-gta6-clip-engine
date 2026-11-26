# ARO-CHAT-0316 — durable report directory-entry synchronization

## Finding

The single-clip CLI exclusively created its primary RUNNING report and flushed/fsynced the file descriptor. The exclusive terminal-fallback writer did the same. Neither path synchronized the containing directory after creating the filename. On POSIX filesystems, a crash after file fsync but before directory fsync can leave the file contents persisted without guaranteeing that the new directory entry survives.

## Change

- Added a shared parent-directory fsync helper.
- Invoke it after file flush/fsync for the primary RUNNING reservation and exclusive terminal-fallback report.
- Directory-sync failures are handled as report-persistence failures and fail closed before media inspection, or are reported through the existing fallback error path.
- Skip directory fsync on Windows because portable Python does not expose a corresponding directory-handle operation. The implementation retains file-level flush/fsync and does not claim Windows directory-entry crash durability.
- Added platform-gated regression coverage.

## Validation

- Repository tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety

Continues existing draft PR #386 and its existing branch/base. No workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, merge, rebase, retarget, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
