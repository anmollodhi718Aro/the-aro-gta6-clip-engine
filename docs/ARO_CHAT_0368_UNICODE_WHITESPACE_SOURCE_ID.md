# ARO-CHAT-0368 | Reject Unicode-Whitespace-Only Candidate Source IDs

- Workstream: ARO-GTA-P0-368; continued on existing draft PR #386 and its original branch/base.
- Added `test_rejects_unicode_whitespace_only_source_id` to `tests/test_candidate_csv_encoding.py`. A source_id containing only U+00A0 NO-BREAK SPACE must be rejected by the existing empty-source-ID validation after Unicode-aware trimming.
- The regression uses a correctly newline-delimited UTF-8 CSV fixture. Existing UTF-8 BOM/CRLF and non-ASCII source-ID preservation tests remain in place.
- Production code unchanged; synthetic CSV only. No media tools, footage, OAuth, credentials, upload, or publishing involved.
- Test commits: `eb5fa0d62002c7620d5378814a3f3ca25018b787` (initial regression) and `b4916c28a1d21a46b41aea794c67913cc739557f` (fixture correction).
- GitHub source read-back confirms the corrected test source. Local unit tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and original ancestry. No workflow retry/dispatch, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
