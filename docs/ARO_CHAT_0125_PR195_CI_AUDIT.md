# ARO-CHAT-0125 PR #195 exact-head CI audit — 2026-11-24

| Field | Record |
|---|---|
| Chat ID | ARO-CHAT-0125 |
| Exact title | ARO-CHAT-0125 | PR #195 Exact-Head CI Audit |
| Workstream ID | ARO-GTA-P1-125 |
| Scope | Audit PR #195's own commit-associated Actions run, Ubuntu/hosted-Windows jobs, compile/tests, synthetic MP4/FFprobe validation, checkout refs, combined status, and review records; documentation-only |
| Branch | `workstream/aro-chat-0125-pr195-exact-head-ci-audit-2026-11-24` |
| Base / starting SHA | PR #195 head `0141f32fcc584e05af5828f461f873667bd7c8d9` |
| Parent PR | #195 |
| Parent base branch | `workstream/aro-chat-0124-pr193-exact-head-ci-audit-2026-11-24` |
| Status | IMPLEMENTED (documentation-only); PR #195 exact-head CI_VERIFIED on merge ref; this follow-up's own exact-head CI PENDING |
| Report | `docs/ARO_CHAT_0125_PR195_CI_AUDIT.md` |
| Scope boundary | No application/uploader/test/renderer/workflow behavior changes; no credentials, OAuth, real media, upload, publishing, merge, retarget, deployment, workflow retry, or destructive action. |

## Exact-head CI evidence

- PR #195 head `0141f32fcc584e05af5828f461f873667bd7c8d9` is associated with Python CI run [#45257788515](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45257788515), run 1024, completed SUCCESS.
- Ubuntu job `137984067440`: compilation passed; 338 unit tests passed (3.477s); synthetic MP4/FFprobe validation passed.
- Hosted-Windows job `137984066970`: compilation passed; 338 unit tests passed (21.670s); synthetic MP4/FFprobe validation passed.
- Both jobs checked out `refs/remotes/pull/195/merge` at merge SHA `5b77a6ae66485dd9de6be78affd77298ca9946c8`. Raw-head-only checkout is NOT DEMONSTRATED.
- Both synthetic reports show a locally generated test pattern/tone, 8.0-second source, 4.0-second rendered output, `gta6_footage_used=false`, `third_party_media_used=false`, `publishing_enabled=false`, and `manual_review_required=true`.
- The same 338-test suite ran on both platforms, not 676 unique tests. Hosted Windows CI is not owner-device verification; synthetic media is not real GTA 6 footage or real-media acceptance.
- Combined commit status returned zero entries. PR #195 review submissions, inline review threads, and conversation comments returned no entries.
- Local tests were NOT RUN in this connector session. PR #193's CI is predecessor evidence only; it is not transferred to PR #195.

## Follow-up branch evidence

- Documentation-only follow-up PR #197 is OPEN / DRAFT / UNMERGED on this branch, based on PR #195's head.
- PR #197 head `72bc3bd688b490b8243c0715642f2ddd00501bc3` had zero associated workflow runs and zero combined-status entries at inspection. Its own exact-head CI remains PENDING / NOT VERIFIED.
- No CI result is claimed for PR #197.

## Safety and owner gates

- Keep PR #197 draft-only. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
- Real-media acceptance, owner-device Windows verification, independent security review, and owner selection of a device-appropriate `--max-upload-bytes` remain outstanding.
- No credentials/tokens, OAuth, real media, network upload, publishing, merge, retarget, deployment, workflow retry, or destructive action was performed.
