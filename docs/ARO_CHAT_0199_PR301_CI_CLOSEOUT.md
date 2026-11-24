# ARO-CHAT-0199 | PR #301 Exact-Head CI Closeout

**Date:** 2026-11-24  
**Chat ID:** ARO-CHAT-0199  
**Workstream ID:** ARO-GTA-P1-199  
**Repository:** `anmollodhi718Aro/the-aro-gta6-clip-engine`  
**Role:** CI evidence auditor; documentation-only

## Scope

Close out the CI verification for PR #301, which adds the missing canonical token-path assertion for the second YouTube destination profile on the current PR #299 test API. No production code changes are included in this audit.

## PR and workflow identity

- PR: [#301](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/301)
- PR branch: `workstream/aro-chat-0198-canonical-profile-path-regression-2026-11-24`
- Audited PR head: `4dce542aa59023a7dc0ca9c61badecf4f0734f59`
- Associated Actions run: [#45399961380](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45399961380), run number 1285, conclusion SUCCESS.
- Both jobs checked out PR merge ref `refs/remotes/pull/301/merge` at merge SHA `d961d60d45337ba58dbcc566b661545c673a5ce7`. This is merge-ref CI evidence; a raw-head-only checkout is not demonstrated.

## Job evidence

### Hosted Windows
- Job ID: `138465637811`; conclusion SUCCESS.
- Compilation succeeded.
- Full suite: `Ran 346 tests in 12.782s`; `OK`.
- The regression `test_profiles_resolve_to_distinct_channel_and_token_paths` passed.
- Synthetic MP4 render and FFprobe validation succeeded.

### Ubuntu
- Job ID: `138465638360`; conclusion SUCCESS.
- Compilation succeeded.
- Full suite: `Ran 346 tests in 3.652s`; `OK`.
- The regression `test_profiles_resolve_to_distinct_channel_and_token_paths` passed.
- Synthetic MP4 render and FFprobe validation succeeded.

Both platform jobs ran the same 346-test suite; this is not 692 unique tests. Both logs report `upload_performed=false`, `gta6_footage_used=false`, `third_party_media_used=false`, `publishing_enabled=false`, and `manual_review_required=true`.

## Conclusion and limits

- PR #301 associated merge-ref CI: PASS on Ubuntu and hosted Windows.
- The missing second-profile token-path regression: PASS in both jobs.
- Raw-head-only CI: NOT DEMONSTRATED.
- Local tests in this connector session: NOT RUN.
- Owner's own Windows device: NOT VERIFIED.
- Real GTA 6 footage / first real clip: NOT VERIFIED.
- OAuth authorization, real upload, public publishing: NOT PERFORMED.

This CI result validates the PR merge-ref path only. It does not authorize merging PR #301, merging its parent PR #299, enabling OAuth/upload, or publishing.

## Safety gates

PR #301 remains OPEN / DRAFT / UNMERGED. PR #299 remains OPEN / DRAFT / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Live uploads and public publishing remain disabled pending independent security review, owner approval, canonical integration, device-specific upload memory limit, and separately authorized real-media acceptance.

No credentials/tokens, OAuth session, real media, network upload, public publishing, merge, rebase, retarget, deployment, or destructive action was performed.
