# ARO-CHAT-0348 | Reject Renderer Success Without a Synthetic Output File

- Workstream: ARO-GTA-P0-348.
- Continuation target: existing draft PR #386 on its original branch and base.
- Starting observed PR head before this continuation: `67e0dd9da31b5abc64cc20f0eb4f2e94c3d68eda`.
- Added `test_main_emits_structured_failure_when_renderer_reports_missing_output` to `tests/test_synthetic_single_clip_smoke.py`.
- The fake renderer reports `status=RENDERED` and a syntactically valid SHA-256 but deliberately creates no output file. The test exercises the public CLI `main()` boundary and requires exit code 1, parseable JSON `FAIL`, the explicit missing-output error, and upload/publishing remaining false.
- This complements the existing empty-output checks by separately covering a false-success report with no artifact at all.
- Production code unchanged. Test commit: `e692439af7428003e4deaf2b7488cc10e47fa784`.
- Serial collision reconciliation: ARO-CHAT-0346 was concurrently assigned to the overflow CLI regression and ARO-CHAT-0347 to unsafe smoke-report guard coverage. This continuation is uniquely assigned ARO-CHAT-0348; the test commit is retained and no history was rewritten.
- Focused report commit: `41242074b8fa42d2cdebe6c106fa1aa3fe45aef3`; registry commit: `878357b5aed3ced236d781c63b5f33435b590362`; startup handoff commit: `120380da75b93d0c12c089dc21b0621ccb46d4b4`.
- Validation: static change/read-back only. Unit tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows verification NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Safety: preserve PR #386 OPEN / DRAFT / UNMERGED and original ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
