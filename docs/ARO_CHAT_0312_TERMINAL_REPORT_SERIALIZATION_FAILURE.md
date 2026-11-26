# ARO-CHAT-0312 — Preserve evidence when terminal JSON serialization fails

- Workstream: `ARO-GTA-P1-312`.
- Continued existing draft PR #386 and branch `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`; no new branch or PR.
- Static review found that the CLI preserved the primary RUNNING report when terminal renderer metadata failed strict JSON serialization, but did not write a separate terminal failure record or warn that a rendered output might already exist. A renderer can return after FFmpeg has completed, then provide malformed metadata such as NaN.
- The CLI now preserves the original RUNNING reservation and attempts to write an exclusive, strict-JSON terminal fallback containing safe failure metadata, the renderer's string status when available, and an explicit output-inspection requirement. It never overwrites an existing fallback or a selected source/output path.
- Regression coverage updates `test_cli_preserves_strict_running_report_when_terminal_json_contains_nan` to simulate a completed render with NaN metadata, verify that the output bytes remain intact, verify that the primary report remains strict-JSON RUNNING, and verify that the separate fallback is strict-JSON FAIL with a manual-inspection warning.
- Production commit: `c87b7dd61d3e41e13318d94d4122cf23cc2b2219`.
- Test commit: `62d6f66974677fc7c064a4d0c8163f5690c176be`.
- Operator documentation commit: `b036e676b8e35e56f799d702a6f9f891ff208d8c`.
- Initial commit messages used provisional 0311 labels; the live registry already assigns ARO-CHAT-0311 to a separate rendered-MP4 metadata regression task. Canonical attribution for this work is ARO-CHAT-0312; no commit history was rewritten.
- Repository tests NOT RUN in this connector session. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows verification NOT VERIFIED; authorized GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and its original base/ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
