# ARO-CHAT-0215: Bind Upload to Approved Video Snapshot

**Workstream:** ARO-GTA-P1-215  
**Branch:** `workstream/aro-chat-0215-approved-video-snapshot-2026-11-24`  
**Base:** PR #324 head `f4cf5766c7f0cad8531919f444d077b2fcdbe0fe`

## Finding
The uploader created a `MediaFileUpload` from a pathname, then validated the durable approval by hashing that pathname. The API media helper could open the pathname later, after the final approval check. A local path replacement in that interval could cause bytes other than the approved bytes to be sent.

## Fix
- Copy the selected video into one private temporary file stream while computing SHA-256.
- Compare the durable owner approval against that snapshot hash.
- Pass the same open stream to `MediaIoBaseUpload`, avoiding a second path lookup.
- Keep the stream open until the API request completes, then close it in `finally`.

## Regression coverage
A mocked API test replaces the original source path after the final approval check and verifies that the bytes consumed by the API client remain the original snapshot bytes.

## Validation status
- Implementation and regression test committed.
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu and hosted-Windows CI: PENDING.
- No OAuth, credentials, real media, network upload, or publishing used.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Live upload and public publishing remain disabled.
