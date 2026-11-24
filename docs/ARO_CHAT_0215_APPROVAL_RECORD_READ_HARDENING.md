# ARO-CHAT-0215 Approval-Record Read Hardening

Date: 2026-11-24

## Finding
Independent review of the snapshot branch found that `require_current_owner_approval()` still used `Path.read_text()` for security-sensitive approval records. That follows symlinks and does not bind the file inspected before opening to the descriptor actually read. The same inherited defect had been addressed on a parallel PR #317 line but was absent from PR #311's consolidated base.

## Changes
- Reject symlink and non-regular approval-record paths.
- Open with `O_NOFOLLOW` and `O_NONBLOCK` where supported.
- Compare pre-open `lstat()` identity with descriptor `fstat()` identity before reading.
- Read JSON from the verified descriptor and close it on every path.
- Add regression coverage for symlink paths, path replacement between stat/open, directories, FIFOs, and FIFO replacement races.

## Commits
- Production: `e20445398a69e2bffb3d58401f3f5a7b322bf10d`
- Tests: `8f6577db86580d4ea90c55736e619262d02302bc`

## Validation
- Local tests: NOT RUN in this connector session.
- CI for the new code/test commits: PENDING.
- Earlier PR #328 run #45426822957 passed 341 tests on Ubuntu and hosted Windows, but it predates this fix and does not validate these commits.
- Earlier CI checked out PR merge ref `fc5b36ab4e395a8f86c5fced36262b1575338790`, merging head `114e5bfc4b154e0da272ed36408ab156cfdc5ab9` into base `67e6d4290fee795fb8ba6fd0e926107ea7f0eb81`. Raw-head-only checkout was not demonstrated.

## Safety
Draft-only. No OAuth, credentials, real media, network upload, merge, deployment, or publishing. Issue #68 remains OPEN; public publishing remains disabled. Owner-device verification and real-media PRIVATE acceptance remain NOT VERIFIED.
