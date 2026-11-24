# ARO-CHAT-0222 — Correct rights-report regression assertion

Date: 2026-11-24

## Identity and scope
- Chat ID: ARO-CHAT-0222
- Chat title: ARO-CHAT-0222 | Fix rights-report regression assertion
- Workstream ID: ARO-GTA-P1-222
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Parent implementation: PR #344
- Base / starting SHA: d2e057734517c1dfb3be994eb7268580f1f173a4
- Branch: workstream/aro-chat-0222-fix-rights-report-regression-assertion-2026-11-24

## Evidence and change
- PR #346 exact-head workflow run #45441375437 failed on Ubuntu and hosted Windows.
- Both jobs compiled successfully, then failed the same test: `test_upload_rechecks_latest_rights_report_before_api_insert`.
- The production guard correctly raised `PermissionError: no recorded rights for source source-2`; the test expected the stale text `no recorded rights for source-2`.
- Updated only the test's expected message to match the observed production error. No production code, workflow, media, OAuth, or uploader behavior changed.
- Commit: 2e79ef7c2a7970cec3259fc200457dc6b3042c92

## Validation
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu / hosted-Windows CI: PENDING.
- No workflow retry/dispatch initiated. Do not transfer PR #346's failed run or any earlier green run to this commit.
- Synthetic MP4/FFprobe validation has not been run on this head.

## Safety
Draft only. No OAuth, credentials/tokens, real media, network upload, publishing, merge, rebase, retarget, deployment, or destructive action. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
