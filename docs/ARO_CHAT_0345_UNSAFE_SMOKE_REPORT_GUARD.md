# ARO-CHAT-0345 | Reject unsafe synthetic smoke renderer reports

- Workstream: ARO-GTA-P0-345; continued existing draft PR #386 on its original branch/base.
- Added `tests/test_synthetic_smoke_safety_contract.py` with one focused regression covering both unsafe report variants: `upload_performed: true` and `publishing_enabled: true`.
- Each case supplies a synthetic output and a matching SHA-256, then requires the smoke harness to reject the report before accepting the output and to remove its temporary directory.
- Production code unchanged. Test commit: `ca897cfe105a6ec636c7ca54b252c9b0cc9d3ec0`.
- Static source/read-back only. Unit tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows verification NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and its original branch/base. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
