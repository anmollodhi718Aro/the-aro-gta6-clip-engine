# ARO-CHAT-0363 | Preserve Valid UTF-8 BOM and CRLF Candidate CSV Exports

- Chat ID: ARO-CHAT-0363
- Workstream ID: ARO-GTA-P0-363
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Parent PR: #386
- Branch: workstream/aro-chat-0244-single-selected-clip-render-2026-11-25
- Scope: test-only regression for valid spreadsheet-export candidate CSV encoding.

## Change

- Added `tests/test_candidate_csv_encoding.py`.
- The regression supplies a UTF-8 BOM and CRLF line endings, then verifies that the explicit selected-row loader accepts the export and returns normalized candidate metadata.
- Production code is unchanged. The test uses a temporary CSV fixture only; it does not open or process media, invoke FFmpeg/FFprobe, render, upload, or publish.

## Commit

- Test commit: `2162adbf6ca952a7f2c74d7c65416b03fd95b4dc`.

## Validation

- GitHub write completed; local test execution NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED.
- Synthetic FFmpeg end-to-end NOT RUN.
- Independent review NOT RECORDED.
- Owner-device Windows NOT VERIFIED.
- Authorized real GTA 6 MP4 NOT PROCESSED.

## Safety and handoff

- Preserve PR #386 OPEN / DRAFT / UNMERGED and its original branch/base ancestry.
- No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
