# ARO-CHAT-0109 | Issue #68 Pre-OAuth Bounded Upload Staging

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0109
- Exact chat title: ARO-CHAT-0109 | Issue #68 Pre-OAuth Bounded Upload Staging
- Workstream ID: ARO-GTA-P1-109
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0109-issue68-pre-oauth-bounded-copy-2026-11-24`
- Base / starting SHA: PR #168 head `9ff25d7356d5badc39f448c9f5e939cda4048541`
- Parent security PR: #168
- Scope: move bounded source staging and immutable byte capture before OAuth interaction; strengthen the oversized-source-growth regression.

## Finding
The PR #168 source-growth regression was described as preventing OAuth/API activity when the source grows beyond the configured upload ceiling, but the uploader called `_authorize_google()` before copying the source into its bounded staging snapshot. The prior test asserted that OAuth was called once, contradicting the stated fail-closed acceptance condition.

## Implementation
- Validate upload flags, privacy, local rights report, and exact clip/source IDs before OAuth.
- Copy the local source incrementally into a private temporary snapshot under `max_upload_bytes`.
- Reject a source that grows beyond the limit during copy; reject an empty staged payload.
- Capture and hash the exact immutable bytes, then clean up the temporary staging directory.
- Only after successful bounded staging, read OAuth client configuration, import the YouTube client, and call `_authorize_google()`.
- Retain authenticated channel verification, exact-byte owner approval, current rights checks, and the repeated identity/approval/rights checks immediately before constructing the upload request.
- Update the regression to require `_authorize_google()` is not called, no token file is created, no upload API request occurs, and the staging directory is removed.

## Verification
- Source and regression test changes committed on the isolated branch.
- Local tests: NOT RUN in this connector session.
- Exact-head GitHub Actions: PENDING; inspect Ubuntu and hosted-Windows jobs and decoded logs before claiming TESTED or CI_VERIFIED.
- No OAuth flow, credentials/tokens, real media, network upload, or publishing was used in this workstream.

## Changed files
- `backend/app/youtube_upload.py`
- `tests/test_youtube_upload.py`
- `docs/ARO_CHAT_0109_ISSUE68_PRE_OAUTH_STAGING.md`
- `docs/CHAT_WORKSTREAM_REGISTRY.md`
- `docs/ARO_CHAT_STARTUP_PROMPT.md`

## Safety and remaining gates
- Draft follow-up only; no merge, retarget, deployment, real upload, or public publishing.
- Issue #68 remains OPEN / UNASSIGNED until owner assignment, independent security review, and owner-controlled integration.
- The owner must still choose a device-appropriate `--max-upload-bytes` before any real upload. The 256 MiB default is not a device-memory guarantee.
- Hosted Windows CI is not owner-device Windows verification. Synthetic media is not GTA 6 footage or real-media acceptance.
