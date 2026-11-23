# ARO-CHAT-0164 | Require an explicit device-selected YouTube upload memory limit

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0164
- Exact title: ARO-CHAT-0164 | Require Explicit Device Upload Memory Limit
- Workstream ID: ARO-GTA-P1-164
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0164-explicit-upload-memory-limit-2026-11-24`
- Base / starting SHA: PR #238 head `cdcf7a4bef2728e3299e82bc88d376992ecec39d`
- Parent security lineage: PR #83 → #87 → #88 → #92 → #93, consolidated through PR #168 and bounded-staging follow-up PR #176; regression repair PR #238.

## Finding
The upload CLI and direct `upload_video()` API previously inherited a 256 MiB default even for a live upload. The project owner must explicitly choose a device-appropriate `--max-upload-bytes` before any real upload. A default value cannot stand in for that owner decision.

## Implementation
- Live CLI uploads now fail closed unless `--max-upload-bytes` is explicitly supplied.
- Direct `upload_video()` calls also require an explicit positive byte limit; callers cannot silently inherit the default.
- Dry-run and approval-only commands retain the documented fallback for local validation and approval preparation; that fallback is not accepted for live upload.
- Added regression coverage for missing CLI and direct-call limits, and made successful mocked upload tests pass an explicit test budget.
- README now explains the device-specific requirement.
- The existing bounded pre-OAuth staging, immutable payload, OAuth owner identity, exact per-clip approval, current rights rechecks, and no-network unit-test boundary remain unchanged.

## Validation
- Local tests: NOT RUN in this connector session.
- Exact-head GitHub Actions: PENDING; inspect this branch's own Ubuntu and hosted-Windows jobs, compile, unit-test count, synthetic MP4/FFprobe and checkout refs.
- Parent PR #238 run #45277658000 passed Ubuntu and hosted Windows (338 tests per platform and synthetic MP4/FFprobe), but that result is predecessor evidence and is not transferred to this branch.
- No OAuth, credentials/tokens, real media, network upload, or publishing was used.

## Safety and remaining gates
- Draft-only follow-up. No merge, retarget, deployment, live OAuth, real media, network upload, public publishing, or destructive action.
- Issue #68 remains OPEN. Keep live/public uploads disabled pending exact-head CI, independent security review, owner-controlled integration, owner-device verification and separate authorized real-media acceptance.
- A device-appropriate upload limit must be selected by the owner before any real upload. This change enforces explicit selection but does not choose the value.
- PR #238 remains the parent test-regression repair; no CI result is transferred between branches or SHAs.
