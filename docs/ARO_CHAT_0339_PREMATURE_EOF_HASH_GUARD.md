# ARO-CHAT-0339: reject premature EOF during synthetic output hashing

- Exact chat title: ARO-CHAT-0339 | Reject Premature EOF During Synthetic Output Hashing.
- Workstream: ARO-GTA-P0-339.
- Continuation target: existing draft PR #386, existing branch `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`, original base unchanged.
- Serial reconciliation: ARO-CHAT-0337 is already assigned to final-`lstat` descriptor cleanup and ARO-CHAT-0338 to initial-path-stat descriptor cleanup. This premature-EOF regression is canonically ARO-CHAT-0339.
- Finding: `_hash_verified_output` must not accept a partial digest if a read unexpectedly returns EOF before the initial regular-file size has been consumed.
- Change: add a regression that simulates an early empty read while file metadata remains unchanged. The helper must reject the incomplete byte count and close its opened descriptor on the failure path.
- Production code unchanged; the existing byte-count check and `finally` descriptor cleanup provide the expected behavior.
- Test: `tests/test_synthetic_single_clip_smoke.py::test_hash_verified_output_rejects_unexpected_early_eof_and_closes_descriptor`.
- Test commit: `168c0e382a48b5172a0d143640405671a1cd5d58`.
- Tests: NOT RUN in this connector session. Synthetic FFmpeg end-to-end: NOT RUN. Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED. Independent review: NOT RECORDED.
- Authorized real GTA 6 MP4: NOT PROCESSED / NOT VERIFIED.
- Safety: preserve PR #386 OPEN / DRAFT / UNMERGED and original base/ancestry. No workflow dispatch/retry, merge, rebase, retarget, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
