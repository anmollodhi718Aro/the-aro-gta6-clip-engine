# ARO-CHAT-0342 | Reject Empty Verified Render Output

- Workstream: ARO-GTA-P0-342.
- Continued existing draft PR #386 on its original branch and base.
- Production change: `scripts/synthetic_single_clip_smoke.py::_hash_verified_output` now rejects a zero-byte file after descriptor/path identity and byte-count stability checks, rather than returning the SHA-256 of an empty payload as a verified output.
- Regression: `tests/test_synthetic_single_clip_smoke.py::test_hash_verified_output_rejects_empty_file` verifies the helper fails closed for an empty file.
- Production commit: `62cb5921de1cdc157dc47bdeef121a99dd3f5074`.
- Test commit: `23111b2d5b9e4a3810b76eb2a6633c2cdf1863f6`.
- Local tests NOT RUN in this connector session. Synthetic FFmpeg end-to-end NOT RUN. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED. Independent review NOT RECORDED. Owner-device Windows verification NOT VERIFIED. Authorized real GTA 6 MP4 NOT PROCESSED.
- Keep PR #386 OPEN / DRAFT / UNMERGED. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
