# ARO-CHAT-0256 — Reject unrepresentable source duration metadata

- Exact chat title: `ARO-CHAT-0256 | Reject Unrepresentable Source Duration`
- Workstream: ARO-GTA-P1-256
- Follow-up to PR #386 / ARO-GTA-P1-244; existing branch and PR preserved.
- Static review found that `math.isfinite()` can raise `OverflowError` for an extremely large Python integer. Although the FFprobe parser rejects overflowing duration conversion, the renderer's preflight boundary must also fail closed independently.
- The source-duration validator now converts `OverflowError`, `TypeError`, and `ValueError` into the existing deterministic invalid-duration report.
- Added a regression using a 401-digit integer duration and asserting a FAIL report, no processing, and no FFmpeg invocation.
- Production commit: `918b14c05d17e3eadbf4f95aee82a60f74891134`.
- Regression-test commit: `44ed0d25553c43ba7c635e1f168bb544b98aeec7`.
- Repository tests NOT RUN in this connector session. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED.
- PR #386 remains DRAFT / OPEN / UNMERGED. Preserve its existing #383 -> #380/#379 ancestry; PR #379 conflicts with the one-selected-video requirement. No merge, rebase, retarget, or integration without owner approval.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled. No real media, OAuth, credentials, upload, publishing, workflow retry/dispatch, or deployment.
