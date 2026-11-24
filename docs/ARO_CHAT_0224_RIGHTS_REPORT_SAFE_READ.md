# ARO-CHAT-0224 — Harden rights-report file reads

Date: 2026-11-24

## Identity and scope
- Chat ID: ARO-CHAT-0224
- Workstream ID: ARO-GTA-P1-224
- Parent: PR #344, revalidate current rights report before upload
- Branch: `workstream/aro-chat-0224-secure-rights-report-read-2026-11-24`
- Base: PR #350 latest branch head `aae75a12b2f921e56ed39acba36de5c669edc5f6`
- Scope: harden local rights-report reads; preserve report validation and upload approval semantics

## Finding
PR #344 re-reads the rights report immediately before the YouTube API insert, but `load_rights_report()` used `Path.read_text()`. A symlink, non-regular path, or pathname replacement during open could redirect the read. A FIFO substituted after an initial path check could also block the uploader.

## Change
- Require the rights report path to be a regular file.
- Open with `O_NOFOLLOW` and `O_NONBLOCK` where supported.
- Compare pre-open pathname identity with the opened descriptor's device/inode.
- Re-check the pathname after open and require it still names the same regular file.
- Parse JSON from the verified descriptor, not by reopening the pathname.
- Preserve existing JSON schema, rights validation, and missing-file behavior.

## Regression coverage
Added mocked filesystem tests for symlink and directory rejection, regular-file replacement between stat/open, FIFO replacement between stat/open, and same-inode symlink substitution after open. Tests use synthetic local files only.

## Validation
- Implementation and tests: committed on the isolated draft branch.
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu / hosted-Windows CI: PENDING.
- Independent security review: NOT RECORDED.
- Owner-device Windows, real-media acceptance and private-upload acceptance: NOT VERIFIED.

## Safety
No credentials or tokens, OAuth session, real media, upload, publishing, merge, rebase, retarget, deployment, or destructive action. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.


## Cross-platform CI correction — 2026-11-24
- Initial PR #353 head `b0d8afedbb6b15e326b7ec309823ca926314c75a` triggered run #45443443832.
- Ubuntu completed compile, unit tests and synthetic MP4/FFprobe successfully.
- Hosted Windows completed compilation but the unit-test step failed; the connector exposed no failing test name or annotation text. Synthetic render was skipped after the test failure.
- Updated the same-inode symlink-substitution regression to simulate the post-open pathname result via a mocked `Path.lstat()`, matching the established approval-record regression pattern and avoiding a physical rename of an open file on Windows.
- Test-only correction commit: `6829261261175dd2f4693b0d8c62685f69fb6298`. Production code unchanged.
- The correction is a portability fix hypothesis pending new exact-head Ubuntu/hosted-Windows CI. Do not claim the previous run passed overall.

## Windows failure log diagnosis — 2026-11-24
- Retrieved the complete Windows job log for run #45443443832 (job 138620636802).
- The failing test was test_rights_report_rejects_same_inode_symlink_substitution_after_open.
- The test attempted to rename preflight.json while its descriptor was open. Windows rejected that operation with PermissionError: [WinError 32] (sharing violation). The resulting mocked open path also produced an expected-message mismatch: the test expected 'regular file', but observed 'rights report changed or became unreadable while opening'.
- This establishes the old test's portability failure; it does not establish a production uploader defect.
- The already-committed correction 6829261261175dd2f4693b0d8c62685f69fb6298 replaces physical rename with a mocked post-open Path.lstat() result. This avoids the Windows open-file rename and tests the post-open symlink rejection branch.
- Corrected-head CI is still NOT VERIFIED: commit-associated workflow lookup for PR #353 head 03071572e8b59bf3f150617e26ea7fd49ca57212 returned zero PR-triggered runs. Do not infer that the correction passed.
- PR #353 review submissions and conversation comments were empty at inspection time. Independent review remains NOT RECORDED.