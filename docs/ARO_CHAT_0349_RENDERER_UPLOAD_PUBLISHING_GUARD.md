# ARO-CHAT-0349 | Reject Renderer Reports That Enable Upload or Publishing

- Workstream: ARO-GTA-P0-349; continuation on existing draft PR #386 and its original branch/base.
- Added `test_smoke_harness_rejects_renderer_report_that_enables_upload_or_publishing` to `tests/test_synthetic_single_clip_smoke.py`.
- The regression runs two isolated cases: a renderer report with `upload_performed=True`, and one with `publishing_enabled=True`. Both reports otherwise claim `RENDERED` and include a matching digest for a non-empty synthetic output.
- Each case must fail closed with the existing “unexpectedly enabled upload or publishing” error. The test also confirms the temporary source, output, and containing directory are removed.
- Production code unchanged. Test commit: `88220548e80283514974c4cf30b781d1d5702f25`.
- Serial collisions: ARO-CHAT-0347 and ARO-CHAT-0348 were already assigned by concurrent work. Earlier misnumbered aliases are marked superseded; this task is uniquely assigned ARO-CHAT-0349. No commit history was rewritten.
- Validation: static edit/read-back only. Unit tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows verification NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Safety: preserve PR #386 OPEN / DRAFT / UNMERGED and original ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
