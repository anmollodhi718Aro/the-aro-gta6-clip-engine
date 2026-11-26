# ARO-CHAT-0372 | Accept Valid Quoted Candidate CSV Headers

- Workstream: ARO-GTA-P0-372.
- Parent: Draft PR #393, whose parent is PR #390. Preserve the existing #393 -> #390 -> #389 -> #388 -> #387 -> #386 ancestry.
- Branch: `workstream/aro-chat-0372-accept-valid-quoted-csv-headers-2026-11-26`.
- Starting SHA: `30f792d5a9ae2d70d5f68714b2c38705a34e481b`.
- Change: added `tests/test_candidate_csv_quoted_headers.py`, a synthetic CSV regression proving correctly quoted required header cells remain accepted by the strict streaming parser and produce the expected selected candidate values.
- Production code unchanged. No media, OAuth, uploader, upload, or publishing behavior changed.
- Test commit: `7226edcbf4fc26137ba435304412639ab2ccad37`.
- Local unit tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: PENDING / NOT VERIFIED.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.
- P0 pipeline: NOT COMPLETE.

## Safety
Keep this work OPEN / DRAFT / UNMERGED. No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
