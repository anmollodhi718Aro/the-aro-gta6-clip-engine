# ARO-CHAT-0251 — Reject boolean clip bounds

- Exact chat title: `ARO-CHAT-0251 | Reject Boolean Clip Bounds`
- Workstream: ARO-GTA-P1-251
- Follow-up to PR #386 / ARO-GTA-P1-244; existing branch and PR preserved.
- Static review found that the low-level `render_clip()` helper passed boolean values to `math.isfinite()`. In Python, `bool` is a subclass of `int`, so `True` and `False` could be silently accepted as numeric clip timestamps by direct callers.
- The helper now rejects boolean start/end bounds before numeric validation or media-path work. Regression coverage checks both boolean values in both positions and verifies FFmpeg is never invoked.
- Production commit: `a329adb4a8232a3bfca2a6d40634b8f64003f126`.
- Regression-test commit: `ff0b081367e57ab1637584017d2828d7cc9557c7`.
- Operator documentation commit: `b0be6062f926d4b5cdcad62207bba92b5c1ab702`.
- Repository tests NOT RUN in this connector session. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED.
- PR #386 remains DRAFT / OPEN / UNMERGED. Preserve its existing #383 -> #380/#379 ancestry; PR #379 conflicts with the later one-selected-video requirement. No merge, rebase, retarget, or integration without owner approval.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled. No real media, OAuth, credentials, upload, publishing, workflow retry/dispatch, or deployment.
