# ARO-CHAT-0201 | PR #311 Exact-Head CI and Security Review

Date: 2026-11-25

## Attribution
- Chat ID: ARO-CHAT-0201
- Workstream ID: ARO-GTA-P1-201
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- PR: [#311](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/311)
- Branch: `workstream/aro-chat-0201-consolidated-private-upload-security-2026-11-24`
- Base: PR #295 head `9f6cdc10bc77e99d6a9399f3c8a1505e18a87ab0`
- Live PR head at inspection: `4aa3c524560c42c42d2b46a50e477ad778286910`
- PR state: OPEN / DRAFT / UNMERGED; GitHub reports mergeable=true.

## Exact-head CI evidence
- Associated Actions run: [#45465185543](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45465185543), completed SUCCESS.
- Ubuntu job `138698094520` and hosted-Windows job `138698094978` both checked out `refs/remotes/pull/311/merge` at merge SHA `909d685311ab40972861ee9239e40b0eb50bb491`.
- The merge SHA combines PR #311 head `4aa3c524560c42c42d2b46a50e477ad778286910` with base `9f6cdc10bc77e99d6a9399f3c8a1505e18a87ab0`.
- Both jobs passed source compilation, the same 340-test suite, and synthetic MP4/FFprobe validation. Ubuntu: 340 tests in 5.683s. Hosted Windows: 340 tests in 16.803s. This is 340 shared test cases executed on two platforms, not 680 unique tests.
- Synthetic reports identify locally generated test pattern/tone only, `gta6_footage_used=false`, `publishing_enabled=false`, and `manual_review_required=true`. Mocked uploader fixtures report `upload_performed=false`.
- Raw-head-only checkout is NOT DEMONSTRATED. Hosted Windows CI is not owner-device Windows verification. Synthetic media is not authorized GTA 6 media or real-media acceptance.

## Bounded static review
Reviewed the complete PR #311 changed-file list and source/test patches:
- `backend/app/youtube_upload.py`
- `tests/test_youtube_upload.py`
- `docs/YOUTUBE_UPLOAD.md`
- `docs/ARO_CHAT_STARTUP_PROMPT.md`
- `docs/CHAT_WORKSTREAM_REGISTRY.md`

The changed upload path preserves the inherited OAuth/OIDC owner and channel verification, exact clip/source/video-hash approval checks, source publish-rights rechecks immediately before the API side effect, and the PRIVATE-only pre-OAuth gate. The response must contain a video ID and explicitly confirm `status.privacyStatus == "private"` before the CLI reports success. The new profile loader rejects configuration and token-directory symlink escapes, and the regression suite restores case-insensitive profile-name uniqueness and profile-specific approval-record directory checks.

No new direct authentication, approval, rights-check, or public-visibility bypass was identified in the bounded changed paths reviewed. This is an engineering static review, not a separate human security sign-off or a claim of exhaustive formal verification.

## Finding / remaining security caveat
**Windows OAuth-token ACL guarantee is NOT VERIFIED.** The new `_persist_oauth_token()` helper calls `os.chmod(..., 0o600)` and ignores `OSError` on the final chmod. On Windows, Python's `os.chmod` does not establish POSIX-style owner-only access-control entries; it primarily controls the read-only attribute. The token file therefore relies on the ACL inherited from its parent directory. The current implementation and hosted-Windows CI do not prove that the owner's local `.secrets/tokens` directory ACL is restricted appropriately. Do not run OAuth or store real tokens until owner-device ACL verification or a separately reviewed Windows ACL implementation closes this caveat.

## Separate owner-selected upload-size gate
PR #311 is based on PR #295 and does not include PR #242's explicit `--max-upload-bytes` enforcement. No device-appropriate limit is selected in this workstream. Keep that separate gate open and do not infer a safe byte limit from the 8 MiB upload chunk size.

## Review and acceptance state
- PR #311 GitHub review submissions: empty.
- PR #311 inline review threads: empty.
- Independent human security sign-off: NOT RECORDED.
- Owner-device OAuth/channel verification: NOT VERIFIED.
- Owner-device Windows token-directory ACL: NOT VERIFIED.
- Explicit device-appropriate upload byte limit: OWNER DECISION PENDING.
- Authorized real-media/private-upload acceptance: NOT VERIFIED.
- Issue #68 remains OPEN. Keep live uploads and public publishing disabled.

## Safety
No OAuth session, credential/token access, real media, network upload, publishing, workflow retry/dispatch, merge, rebase, retarget, deployment, or destructive action was performed. PR #311 remains draft-only.
