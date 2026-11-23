# ARO-CHAT-0106: Issue #68 canonical security branch and rights-registry hardening

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0106
- Exact chat title: ARO-CHAT-0106 | Issue #68 Security Consolidation and Rights Registry Hardening
- Workstream ID: ARO-GTA-P1-106
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0106-issue68-rights-registry-hardening-2026-11-24`
- Base / starting SHA: PR #162 head `546906fca62ff2493a7ae1955dfdd1b4948233f2`
- Scope: security-lineage audit, canonical candidate selection, fail-closed source-rights registration, and offline regression tests.

## Audit and selection
- PR #82 is retained as a parallel reference, not selected: its reviewed approval model lacks the full Google OIDC subject, exact-file digest, privacy binding, and approval-expiry binding.
- The stronger authenticated uploader lineage is PR #83 → #87 → #88 → #92 → #93.
- PR #87 fixes the recursive Google OIDC verifier; #88/#92 bind upload to the exact approved immutable bytes; #93 adds an incremental upload-size ceiling.
- PR #93 exact head `f9834d29235738573ad773f19ebcc9b7c0f4c129` has successful Actions run #45020379946 on Ubuntu and hosted Windows, including compile, full unittest steps, and synthetic MP4/FFprobe validation. No numeric test count is claimed.
- PR #96 adds a direct-call size guard test. PR #105 identified further coverage gaps. PRs #106–#109 overlap; #106 had the broadest integrated coverage, while #107–#109 are narrower or duplicate variants. The current continuation branch includes the direct-call guard lineage and adds the missing integrated source-growth/staging-cleanup regression rather than stacking a second duplicate test PR.
- PR #162 is the latest documentation/audit baseline in this conversation's live repository view; its exact head had no associated workflow run at inspection. Its CI result is not inferred from neighboring PRs.
- Canonical candidate for subsequent owner review: this branch, built on PR #162's current documentation baseline and retaining the PR #83→#93 implementation ancestry, with the source-rights fix and focused regression coverage. PR #82 and duplicate test branches remain preserved; no merge/closure/retarget is performed.

## Security finding and implementation
The existing `SourceRightsRegistry.register()` used `ON CONFLICT(source_id) DO UPDATE` and set `revoked_at=NULL`. A repeated registration could therefore replace an existing grant and silently clear revocation.

Changes:
- Make `register()` append-only: an existing `source_id` raises `PermissionError`; no row is updated and revocation cannot be cleared.
- Treat `source_id` as a unique, versioned grant identifier. A new grant after revocation must use a new versioned ID, and downstream rights reports/approvals must bind to that new ID.
- Record grantor and evidence reference in the registration audit event.
- Add regression tests for duplicate active-grant overwrite rejection, revoked-grant reactivation rejection, and explicit new-version registration.
- Add a synthetic upload-path growth regression proving that a source which grows after the initial stat is rejected during bounded copy, the staging directory is cleaned, and OAuth/API upload is never reached.

## Verification status
- Local tests: NOT RUN in this connector session.
- Exact-head GitHub Actions: pending; this PR must be checked on its own final head.
- Tests are offline/synthetic and use mocked YouTube clients; no network upload is performed.
- Owner-device Windows, real-media acceptance, live OAuth, and actual upload are NOT VERIFIED / NOT PERFORMED.

## Owner and safety gates
- Issue #68 remains open. This branch does not merge, close, or retarget any PR.
- Keep public uploads disabled until the selected branch passes exact-head CI, independent review, and owner-controlled integration.
- Before any real upload, the owner must select a device-appropriate `--max-upload-bytes` value; 256 MiB is not a universal device-memory guarantee.
- A new versioned source grant requires genuine, documented permission evidence. The `actor` field is audit metadata, not authentication of the grantor.
- No credentials/tokens, live OAuth session, real media, network upload, public publishing, deployment, merge, destructive action, or collaborator permission change was performed.


## Exact-head CI closeout — 2026-11-24

- Final PR head `9ff25d7356d5badc39f448c9f5e939cda4048541` is associated with Python CI run [#45245685334](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45245685334), completed SUCCESS.
- Ubuntu job `137941689306`: compile passed; 338 unit tests passed; synthetic MP4 render and FFprobe validation passed.
- Hosted Windows job `137941688716`: compile passed; 338 unit tests passed; synthetic MP4 render and FFprobe validation passed.
- Both jobs completed all setup, compile, test, and synthetic-render steps successfully. The same 338-test suite ran on each platform, not 676 unique tests.
- Synthetic evidence: `gta6_footage_used=false`, `third_party_media_used=false`, `publishing_enabled=false`, `manual_review_required=true`.
- Status: IMPLEMENTED and CI_VERIFIED on this exact PR head. Hosted Windows CI is not owner-device verification; synthetic media is not real GTA 6 footage.
- Remaining gates: independent security review, owner-controlled integration approval, owner selection of a device-appropriate `--max-upload-bytes`, and separate real-media acceptance. Issue #68 remains OPEN; keep live uploads/public publishing disabled.
- No credentials, live OAuth, real media, network upload, publishing, merge, retarget, deployment, or destructive action was performed.
