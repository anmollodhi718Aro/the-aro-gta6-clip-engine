# ARO-CHAT-0364 | Reject Malformed Trailing Candidate CSV Rows

Date: 2026-11-26

- Workstream: ARO-GTA-P0-364; continued existing draft PR #386 on its original branch/base.
- Serial-collision reconciliation: concurrent work registered ARO-CHAT-0363 for whitespace candidate CSV header rejection. This trailing-row parser regression is uniquely registered as ARO-CHAT-0364. The provisional `docs/ARO_CHAT_0363_STRICT_TRAILING_CSV_ROWS.md` remains a historical alias; no commit history was rewritten.
- Reviewed `load_selected_candidate()`: it parses the complete candidate CSV before returning the selected row, so malformed later records cannot be hidden by selecting an earlier valid row.
- Added `tests/test_candidate_csv_strict_trailing_rows.py`. The fixture contains a valid selected first row followed by an unterminated quoted field in a later row. The regression requires the loader to reject the entire CSV with its structured read-error boundary.
- Production code unchanged. Synthetic CSV text only; no media tools, real footage, credentials, upload, or publishing involved.
- Test commit: `a5c609ae6608a77cfe1009f6f7792914306c76c8`; canonical report commit: pending.
- GitHub source read-back confirms the test file is present. Local unit tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and original ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
