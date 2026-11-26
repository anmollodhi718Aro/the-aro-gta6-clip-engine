# ARO-CHAT-0313 — terminal serialization fallback regression

- Date: 2026-11-26
- Workstream: ARO-GTA-P1-313
- Continued existing draft PR #386 and branch `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`; no new branch or PR.
- The preceding implementation commit `c87b7dd61d3e41e13318d94d4122cf23cc2b2219` preserves the primary RUNNING report when terminal result serialization fails and attempts to write a separate exclusive strict-JSON failure record.
- Added `tests/test_single_clip_render_terminal_serialization.py` to force a non-JSON terminal result and verify:
  - the primary report remains parseable and retains RUNNING status;
  - the separate fallback is parseable strict JSON, newline-terminated, and marked FAIL;
  - the fallback records that terminal serialization failed and output inspection is required;
  - upload and publishing remain disabled; and
  - the CLI returns the documented failure exit code without creating output.
- Test file commits: `cc79bf7f921ae6448c5536e07d1bd5956449b3e9`, followed by assertion correction `b5b474da98d65be0bf92d86793baf5c43a95d21a`.
- Production behavior unchanged by this workstream.
- Tests NOT RUN in this connector session. Exact-head Actions lookup currently returns zero workflow runs for the latest test commit; CI NOT VERIFIED. Independent review NOT RECORDED.
- No real media, OAuth, credentials, upload, publishing, workflow retry/dispatch, merge, rebase, retarget, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
