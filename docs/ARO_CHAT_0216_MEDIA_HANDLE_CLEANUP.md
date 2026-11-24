# ARO-CHAT-0216 | Close resumable media handle before snapshot cleanup

Date: 2026-11-24

## Finding

PR #328 stages the approved video bytes in a private temporary directory and passes that filename to Google's resumable `MediaFileUpload`. The media helper retains an open file handle for chunked reads. The upload function's `finally` block previously attempted to remove the temporary directory without first closing that handle. On Windows, an open handle can prevent deletion and cause cleanup to raise after the API request has already returned a verified PRIVATE response.

## Change

- Initialize the media object before entering the upload block.
- In the cleanup path, close the retained `MediaFileUpload._fd` stream when present.
- Use a nested `finally` so snapshot directory cleanup is still attempted if stream close raises.
- Extend the source-mutation regression test so the mock media helper holds a real open file object and assert that it is closed when the upload function returns.

## Workstream

- Chat ID: ARO-CHAT-0216
- Workstream ID: ARO-GTA-P1-216
- Branch: `workstream/aro-chat-0216-close-upload-media-handle-2026-11-24`
- Base: PR #328 head `114e5bfc4b154e0da272ed36408ab156cfdc5ab9`
- PR: [Draft PR #333](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/333)

## Validation

- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu and hosted-Windows CI: PENDING.
- No OAuth, real media, network upload, merge, deployment, or publishing used.
- Real-media PRIVATE acceptance remains NOT VERIFIED.

## Safety

Draft-only follow-up. Issue #68 remains OPEN. Keep live uploads and public publishing disabled pending independent security review, owner-controlled integration, owner-device verification, source-rights evidence, and separately authorized real-media PRIVATE acceptance.
