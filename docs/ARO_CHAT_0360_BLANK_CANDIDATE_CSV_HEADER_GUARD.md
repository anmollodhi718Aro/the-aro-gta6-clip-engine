# ARO-CHAT-0360 | Reject Blank Candidate CSV Header Cells

- Workstream: ARO-GTA-P0-360; continued on existing draft PR #386 and its original branch/base.
- Serial reconciliation: ARO-CHAT-0359 / ARO-GTA-P0-359 was concurrently registered for a separate output-descriptor read-failure cleanup regression. This blank-header validation change is uniquely attributed to ARO-CHAT-0360 / ARO-GTA-P0-360. No commit history was rewritten; the provisional `docs/ARO_CHAT_0359_BLANK_CANDIDATE_CSV_HEADER_GUARD.md` filename is retained as a historical alias.
- Static review found that `csv.DictReader.fieldnames` represents an empty header cell as `None`. The previous blank-header check converted each header to text before checking emptiness, so `None` became the non-empty string `"None"` and a malformed trailing header cell could pass schema validation.
- Updated `backend/app/single_clip_render.py` to reject `None` header cells explicitly, while retaining blank-string and duplicate-header rejection.
- Added `test_candidate_csv_rejects_blank_header_cells` in `tests/test_single_clip_render.py`. The fixture has all required columns plus a trailing empty header cell and an extra row value; loading must fail with the existing blank/duplicate-header validation error.
- Production commit: `332fed855b6bdee0577bae5271d428cd8dfcaf2a`.
- Regression test commits: `5c31bb716fe1634ea520312e94f38522ca95d39e` and newline-fixture correction `99ad110f15bd27eec8da5f443b267a4366ff0d9b`.
- Canonical report: `docs/ARO_CHAT_0360_BLANK_CANDIDATE_CSV_HEADER_GUARD.md`.
- Static source read-back confirms the guard and test fixture are present. Unit tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and original ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
