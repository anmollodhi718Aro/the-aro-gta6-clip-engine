# ARO-CHAT-0316 — Snapshot Path Resolution Failure Containment

- Workstream: ARO-GTA-P1-316. Continued existing draft PR #386 and its existing branch; no duplicate branch or PR.
- Static review found `_create_stable_source_snapshot()` normalized only `OSError` from `Path.resolve()`. Python can also raise `RuntimeError` for symlink loops and `ValueError` for malformed paths.
- The helper now converts all three resolution exception classes into a deterministic `ValueError` validation failure before opening or creating the snapshot.
- Regression: `test_snapshot_path_resolution_symlink_loop_is_normalized` injects a resolution loop, checks the controlled error, verifies the selected source remains unchanged, and verifies no snapshot is created.
- Production commit: `3dd984e568145ce41abd52fc07352d40ff4f59ea`.
- Test commit: `a2f88deb56974054424c7c2d51c7937d7b2c0fa4`.
- Operator guide: `7a3dc5cb5e85181bb9dfe0140d4914350c230354`.
- Registry: `af56c35d9354d805ca4f4bdd948896acdb8eb259`.
- Startup handoff: `5e98b185ce392ee11e010238172fc0c0d05c5d9d`.
- Local tests NOT RUN. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED. Independent review NOT RECORDED. Owner-device Windows verification NOT VERIFIED. Authorized real MP4 NOT PROCESSED.
- PR #386 remains OPEN / DRAFT / UNMERGED with original base and ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled.
