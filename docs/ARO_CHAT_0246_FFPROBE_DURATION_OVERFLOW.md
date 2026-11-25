# ARO-CHAT-0246 — FFprobe duration conversion overflow regression

- Chat ID: ARO-CHAT-0246
- Follow-up to: PR #386 / ARO-GTA-P1-244
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Finding: an extremely large JSON integer in FFprobe's `format.duration` can raise `OverflowError` during float conversion. The previous exception boundary did not catch it, so malformed metadata could escape the intended deterministic FAIL report.
- Change: include `OverflowError` in the FFprobe metadata validation exception boundary.
- Regression: use a 401-digit JSON integer duration and assert the preflight returns FAIL with an invalid-metadata error.
- Production commit: `7b9f05fdbe479018351c93e31025762550364312`
- Test commit: `7456ff5beb5a63893654c0867d5f4676514ee071`
- Tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- No media processed, no OAuth or credentials, no upload/publishing, no workflow retry/dispatch, no merge/rebase/retarget/deployment.
- PR #386 remains draft/open/unmerged. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing stay disabled.
