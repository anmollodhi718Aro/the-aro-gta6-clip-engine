# Independent YouTube Uploader Security Audit

**Date:** 2026-11-22  
**Chat ID:** ARO-CHAT-0047  
**Workstream ID:** ARO-GTA-P1-47  
**Role:** Independent static security reviewer  
**Repository:** `anmollodhi718Aro/the-aro-gta6-clip-engine`  
**Base:** PR #94 branch `workstream/aro-chat-0046-exact-head-ci-closeout-2026-11-22`  
**Starting SHA:** `93ca44365b111fb9ce5a6dd0be8bd7aa6ab0bf50`

## Scope and limits

Review the competing authenticated YouTube uploader implementations and the currently stacked remediation line for Issue #68. This is a source-level review of the exact branches named below, not a penetration test, live OAuth test, or authorization to upload. No application source or tests were changed.

Reviewed:
- PR #82 / ARO-CHAT-0039, head `f0f1976eab6db2d428152eba220078e5a4893a9b`
- PR #83 / ARO-CHAT-0038, head `f66f6406a496d08e3e85972010f1f52d831298ab`
- PR #93 / ARO-CHAT-0045, head `f9834d29235738573ad773f19ebcc9b7c0f4c129`
- PR #94 / ARO-CHAT-0046, head `93ca44365b111fb9ce5a6dd0be8bd7aa6ab0bf50`
- Issue #68 and the current registry/startup prompt.

## Findings

### F-1: PR #82 is not an equivalent security implementation to the PR #83 lineage

PR #82 resolves a YouTube channel through the OAuth-authenticated `channels.list(mine=True)` response and compares it with a configured channel ID. Its approval record binds clip ID, source ID, decision, reviewer string/channel identity, and review timestamp. The reviewed model does not bind the approval to a Google OIDC subject, destination privacy level, exact video digest, or approval expiry.

**Risk:** channel-level identity is weaker than a stable authenticated human principal, and the approval can be reused for changed bytes or another privacy level unless additional controls exist outside the reviewed model.

**Disposition:** do not select PR #82 as the canonical implementation without an explicit owner-approved redesign that closes these gaps.

### F-2: PR #83's reviewed head contains a recursive OIDC helper defect

At PR #83 head `f66f6406a496d08e3e85972010f1f52d831298ab`, `_verify_google_id_token()` calls itself recursively. The primary channel-owner verification path duplicates token verification inline, so tests that exercise only the primary path can miss the broken helper.

**Remediation lineage:** PR #87 contains the helper correction in the PR #83 stack. PR #91 is a parallel fix for the same defect. Preserve both histories; do not independently integrate both. The PR #93 stack descends through the PR #87 remediation path.

### F-3: PR #83's original path-based upload has a hash/upload TOCTOU gap

The PR #83 uploader creates a path-based `MediaFileUpload` and validates the approval against a file hash, but the API client later reads the path. The file can change between validation and media consumption.

**Remediation lineage:** PR #88 stages the source, PR #92 binds the upload to an immutable byte payload, and PR #93 adds a configurable size ceiling plus incremental copy-time enforcement. The PR #93 implementation hashes the immutable bytes and gives those same bytes to `MediaIoBaseUpload`, then repeats owner, approval, and current-rights checks immediately before request construction.

### F-4: Upload memory ceiling still needs owner/device configuration

PR #93 defaults to 256 MiB and supports `--max-upload-bytes`. The uploader captures the staged payload in memory, so the ceiling bounds that payload but does not prove the default is appropriate for a particular device or total process memory.

**Required owner action:** choose a conservative value based on actual available RAM, other running applications, and expected clip sizes before any real upload. Do not infer that 256 MiB is safe for every machine.

### F-5: Approval gates remain operationally unresolved

Issue #68 remains open. The registry records parallel draft PRs and explicitly requires independent review and owner-controlled canonical selection. Static code review does not authorize a merge, OAuth setup, real upload, public publication, or closure of Issue #68.

## Recommendation

Use the PR #83 lineage as the stronger security design candidate, but evaluate the *stacked remediation candidate* rather than the original PR #83 head. Specifically, review the PR #87 OIDC-helper fix and the PR #88 → #92 → #93 immutable-upload and memory-bound changes together. Keep PR #82 preserved as a parallel historical implementation; do not merge it independently.

Before any integration:
1. Owner explicitly selects the canonical PR/branch or approves a consolidation plan.
2. Independent reviewer verifies the exact selected head and its complete acceptance tests.
3. Owner chooses a device-appropriate upload-size ceiling.
4. Keep live uploads and public publishing disabled until OAuth owner identity, exact clip/source/file/privacy approval, current source rights, and all acceptance tests are verified.

## Verification status

- Static source review: **COMPLETE for the listed snapshots**.
- Dynamic security testing: **NOT RUN**.
- Local tests in this workstream: **NOT RUN**.
- New branch CI: **NOT RUN**; this workstream changes documentation only.
- PR #93 exact-head CI: the existing registry records successful run `45020379946` on `f9834d29235738573ad773f19ebcc9b7c0f4c129`; this is inherited evidence for that exact PR #93 head only, not a new run for this branch.
- Owner-device verification: **NOT VERIFIED**.
- Real-media verification: **NOT VERIFIED**.
- Live OAuth/upload/public publishing: **NOT PERFORMED**.

## Safety boundary

No credentials, tokens, or real media were accessed. No network upload, public publishing, merge, retarget, deployment, branch deletion, or destructive action was performed. Issue #68 remains open pending owner action.
