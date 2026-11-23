# ARO-CHAT-0122 | PR #190 Exact-Head CI Audit

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0122
- Exact title: ARO-CHAT-0122 | PR #190 Exact-Head CI Audit
- Workstream ID: ARO-GTA-P1-122
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0122-pr190-exact-head-ci-audit-2026-11-24`
- Base / starting SHA: PR #190 head `2252a570d93108d42a5ad0b6890fcfb8cff7f304`
- Parent PR: #190, the ARO-CHAT-0119 audit follow-up for PR #189

## Scope
Audit PR #190's own commit-associated Actions run, Ubuntu/hosted-Windows compile and test results, synthetic MP4/FFprobe evidence, checkout refs, combined status, and review records. Documentation-only; no application, uploader, test, renderer, or workflow behavior changes.

## Exact-head CI evidence
- PR #190 head `2252a570d93108d42a5ad0b6890fcfb8cff7f304` is associated with Python CI run [#45256749454](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45256749454), run 1014; conclusion SUCCESS.
- Ubuntu job `137980462168`: setup, checkout, Python, FFmpeg/FFprobe installation, compilation, unit tests, and synthetic MP4/FFprobe steps all succeeded. Decoded log: 338 tests passed in 5.305s.
- Hosted-Windows job `137980462832`: setup, checkout, Python 3.11, FFmpeg/FFprobe installation, compilation, complete unittest suite, and synthetic MP4/FFprobe steps all succeeded. Decoded log: 338 tests passed in 12.648s.
- Both jobs checked out `refs/remotes/pull/190/merge` at merge SHA `0694098bf7f5e6e22cbd960d6505dd2dba93f021`, merging PR #190 head into base `d15fcfbcf02883c26a2b61710576f5f6ce369ed1`. Raw-head-only checkout is NOT DEMONSTRATED.
- Synthetic report on both platforms: `gta6_footage_used=false`, `third_party_media_used=false`, source duration 8.0 seconds, rendered duration 4.0 seconds, `publishing_enabled=false`, `manual_review_required=true`.
- The same 338-test suite ran on each platform, not 676 unique tests. Hosted Windows CI is not owner-device Windows verification; synthetic media is not real GTA 6 footage.

## Review and status
- PR #190 remains OPEN / DRAFT / UNMERGED.
- Combined commit status returned no status entries.
- PR #190 review submissions and inline review threads returned empty lists at inspection; independent review is NOT RECORDED.
- Local tests were NOT RUN in this connector session. The hosted CI evidence above is exact-head-associated but ran against the PR merge ref, not a raw-head-only checkout.

## Safety and remaining gates
- Documentation-only audit; no application or uploader behavior changed.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled until owner-controlled security review and integration approval.
- No credentials/tokens, live OAuth, real media, network upload, public publishing, merge, retarget, deployment, workflow retry, or destructive action was performed.
- Real-media acceptance, owner-device Windows verification, independent security review, and owner selection of a device-appropriate `--max-upload-bytes` remain outstanding.
