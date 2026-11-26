# ARO-CHAT-0363 | Reject Unicode Whitespace Candidate CSV Headers

- Workstream: ARO-GTA-P0-363; continued on existing draft PR #386 and its original branch/base.
- Added `test_rejects_unicode_whitespace_only_header_cell` to `tests/test_candidate_csv_blank_headers.py`.
- The synthetic CSV fixture uses a non-breaking space (U+00A0) as a header cell. The parser must reject it with the existing blank/duplicate-column validation error, exercising Python's Unicode-aware `str.strip()` behavior rather than only ASCII whitespace.
- Production code unchanged; temporary CSV fixtures only; no FFmpeg/FFprobe process or media used.
- Test commits: `040a8b0423180c82f987ac1815f78a8dfe61423a` (initial addition) and `2be4e4a5d28124bcaeeb079fb9c0ed7c586925ab` (fixture newline correction).
- GitHub source writes completed. Local unit tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and original ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
