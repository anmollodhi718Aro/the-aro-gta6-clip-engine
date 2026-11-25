# ARO-CHAT-0240 | Bounded PRIVATE upload and Windows token ACL

Date: 2026-11-25

## Scope and lineage
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Continuation branch: `workstream/aro-chat-0240-private-upload-size-and-windows-token-acl-2026-11-25`
- Parent candidate: PR #311, based on PR #295 ancestry.
- Continuation starts from PR #311 head `e2e04bfe054b10d8fee5d5fe4244aa8dac9d56fa`.
- Draft follow-up PR has not yet been opened at the time this report is created.

## Implemented changes
1. Actual upload requires a positive explicit `--max-upload-bytes` value. No default is assumed for the owner's hardware.
2. `validate_upload` checks the selected limit before any upload attempt.
3. Upload staging copies in 1 MiB chunks to a temporary disk snapshot, rejecting a source that exceeds the limit while being copied. It does not buffer the entire video in RAM.
4. The same staged snapshot is used for the OAuth-bound approval hash and the YouTube upload request, and is removed after the attempt.
5. On Windows, token directory/file DACLs are protected from inheritance and restricted to the current user and LocalSystem. The ACL is read back and checked; failure is fail-closed.
6. Added tests for required/positive limits, oversized source rejection, snapshot byte identity and cleanup, and Windows ACL success/failure behavior.

## Validation state
- Source/test changes are committed to the continuation branch.
- Local repository tests: NOT RUN.
- Exact-head Ubuntu CI: NOT VERIFIED.
- Exact-head hosted-Windows CI: NOT VERIFIED.
- PowerShell ACL behavior: NOT YET VERIFIED on a Windows runner.
- No tests or CI pass are claimed by this report.

## Security review caveats
- This is a code implementation candidate, not independent human security sign-off.
- Hosted Windows CI does not substitute for owner-device verification of the actual Windows account and filesystem environment.
- The owner must choose a suitable `--max-upload-bytes` value for the device before any upload attempt.
- Existing OAuth/channel identity, per-clip approval, exact source/video hash binding, PRIVATE-only response verification, and current source-rights checks remain required.
- A successful synthetic test does not prove authorized real-media acceptance.

## Safety state
- No OAuth session started and no credentials/tokens accessed.
- No real media processed.
- No network upload or publishing performed.
- No merge or deployment performed.
- Live uploads and public publishing remain disabled.
