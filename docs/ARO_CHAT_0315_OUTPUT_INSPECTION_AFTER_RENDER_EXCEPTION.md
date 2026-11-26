# ARO-CHAT-0315 — output inspection warning after renderer exceptions

- Workstream: ARO-GTA-P1-315; continued existing draft PR #386 and branch `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`.
- Static review found that the CLI's ordinary renderer-exception handler preserved the configured output path and warned in prose, but omitted the machine-readable `output_inspection_required=true` field. The renderer may create or publish an output before raising, so downstream operators could not reliably distinguish this failure from one with no possible output.
- Production change: renderer-exception FAIL reports now set `output_inspection_required=true`; snapshot creation/verification remain unknown when no structured renderer result is returned. Existing output is not deleted or overwritten.
- Regression: `test_cli_marks_output_inspection_required_when_renderer_raises_after_output_creation` simulates a possible output being created before an exception, then verifies the FAIL report flag, output-path preservation, output-byte preservation, and disabled upload/publishing.
- Production commit: `9b396cda964b507b294dca99d4f3f3a83940e7bf`.
- Test commit: `16cda8f75b266842c751f0582d4862c2e3f47713`.
- Local tests NOT RUN in this connector session. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows verification NOT VERIFIED; authorized real MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and its original base/ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
