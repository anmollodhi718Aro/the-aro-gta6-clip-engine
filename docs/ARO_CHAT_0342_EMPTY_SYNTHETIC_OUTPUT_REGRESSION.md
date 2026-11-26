# ARO-CHAT-0342 | Reject Empty Synthetic Render Output

- Workstream: ARO-GTA-P0-342.
- Continuation target: existing draft PR #386 on its original branch and base.
- Finding addressed: the smoke harness already rejects a zero-byte output after independently hashing it, but this safety boundary lacked a direct regression test.
- Change: add a synthetic renderer fixture that creates an empty output and reports the matching SHA-256 of empty bytes; assert the smoke harness still fails with the explicit empty-output error. This proves a matching digest alone cannot make an empty artifact pass.
- Production code unchanged. Upload and publishing remain disabled.
- Test-file commit: `52ec6e2df704d0ca6ed6cb0cf37f5b1700a05d5e`.
- Validation: tests NOT RUN in this connector session; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows verification NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Safety: preserve PR #386 OPEN / DRAFT / UNMERGED and original ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
