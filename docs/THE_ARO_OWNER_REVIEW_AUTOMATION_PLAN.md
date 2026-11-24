# THE ARO Owner-Review Automation Operating Plan

Date: 2026-11-24

## Owner's operating goal

Build THE ARO GTA 6 Clip Engine as an end-to-end automation system. The owner should normally only review finished outputs in the Studio/Dashboard and handle exceptional decisions or required approvals. The system, not an individual ChatGPT conversation, is the durable source of workflow state.

The owner has explicitly requested that four separate GPT-enabled devices/sessions can resume work by pasting the standard startup instruction:

`THE ARO GTA 6 Clip Engine की GitHub Master Script और Chat Workstream Registry पढ़ो। Latest pending task identify करो और सुरक्षित तरीके से coding शुरू करो।`

Every session must read the current GitHub Master Script/startup prompt, workstream registry, current open PRs, branches and CI before choosing a task. Never rely on chat memory, stale summaries, or copied task text as the source of truth.

## Intended automation pipeline

1. **Authorized source intake**: accept only owner-provided or explicitly licensed source media and authorized platform data. Record source identity, rights evidence, permitted scopes, expiry and revocation.
2. **Analysis and candidate detection**: identify events/highlights, timestamps, evidence and confidence; preserve traceability to source assets.
3. **Clip planning**: propose safe clip bounds, aspect ratio, duration, captions/subtitle and edit plan. Do not silently publish or expand rights.
4. **Rendering and validation**: render locally with bounded settings; validate output streams, duration, dimensions, audio and file integrity; retain logs and provenance.
5. **Metadata preparation**: generate channel-appropriate titles, descriptions, subscribe prompts, hashtags and thumbnail candidates. Treat metadata as editable drafts.
6. **Owner review studio**: present preview, source/provenance, rights status, metadata and validation results in one queue. The owner reviews finished clips and handles only exceptions/important decisions.
7. **Private upload staging**: after the upload security gate is implemented and verified, upload approved clips as PRIVATE to each explicitly authorized target channel. Keep a per-channel upload record and verify the returned video ID and privacy status. Never infer channel ownership from a handle alone.
8. **Separate public decision**: after the owner reviews the private upload in YouTube Studio, the owner alone decides whether to change visibility to Public. Public publishing must require a separate explicit owner action; a private-upload approval is not public-publishing approval.

## Initially requested YouTube targets

- `@aroanmol7`
- `@the_arro07`

These are owner-supplied target handles, not proof of authenticated ownership. Before enabling uploads, bind each target to its authenticated YouTube channel ID using the approved OAuth/owner-verification flow. Require explicit per-channel authorization and per-video approval. Do not ask for passwords or expose OAuth tokens in chat, commits, logs or registry.

## Four-device / multi-GPT coordination rules

- All four GPT sessions use this same repository, Master Script and registry. GitHub is the shared durable memory.
- At startup, read the full relevant instructions, latest registry tail, open PRs and active branches; identify the newest actionable pending task and report its exact Chat ID, Workstream ID, branch, base SHA and blocker.
- Reserve a unique Chat ID and bounded workstream before edits. One chat owns one workstream and one branch. Never let two sessions edit the same branch or same file concurrently.
- Prefer independent bounded tasks. For shared planning files, serialize changes through separate branches/PRs and re-fetch latest content before each write. Do not copy stale file contents between sessions.
- Each session must record changes, commits, tests actually run, exact-head CI, review status and remaining blockers. Do not infer success from another branch's CI.
- If no safe independent task exists, perform a read-only audit and report the blocker rather than inventing work.
- The owner should not need to coordinate low-level code tasks across devices; the registry assigns work and prevents duplication. Owner approval remains required for rights, channel binding, upload authorization, merge, deployment and public visibility.

## Required release gates

- No live YouTube upload until Issue #68's authenticated channel-owner and per-clip authorization requirements are implemented, independently reviewed, and accepted.
- Verify OAuth identity maps to the exact channel ID, not merely a supplied handle.
- Bind each approval to the exact rendered asset hash, source asset/rights record, destination channel ID, intended visibility (PRIVATE), and metadata snapshot.
- Re-check scopes, expiry, revocation, destination channel and asset hash immediately before upload. Fail closed on mismatch, missing evidence, expired/revoked permission or uncertain status.
- Use idempotency/deduplication so retries cannot create duplicate uploads. Persist upload outcome and returned video ID; verify privacy status after upload.
- Default and enforce PRIVATE visibility. No scheduled/public/unlisted visibility unless the owner explicitly selects that mode for that exact clip. Public requires a distinct final owner action after review.
- Keep a global kill switch and per-channel disable switch. Log actions without logging secrets. Provide dry-run mode.
- Never enable unattended publishing, bypass platform policy, scrape unapproved sources, or use third-party media without documented rights.

## Current implementation boundary / next work

This document is a product operating plan, not evidence that the pipeline or upload integration already exists. The local authorized MVP and renderer are separate from the secure live uploader. Issue #68 remains the blocking security gate. Do not enable real uploads merely because this plan or the owner's general automation request is recorded.

Next sequence:
1. Preserve and review the current Issue #68 security PR lineage; select/consolidate one canonical implementation only after independent review and explicit owner approval.
2. Complete authenticated channel identity binding and per-clip private-upload authorization.
3. Implement private upload staging, idempotency, post-upload privacy verification and audit ledger.
4. Build the review dashboard and owner exception queue.
5. Add integration tests with mocked YouTube responses, then owner-authorized test-channel validation. Keep public publishing disabled.
6. Only after the owner has inspected a private upload may the owner independently change it to Public.

## Acceptance criteria for the intended owner experience

- A fresh GPT session on any of the four devices can identify the latest pending task from GitHub without asking the owner to restate project context.
- Duplicate workstream reservations and concurrent shared-file edits are prevented or detected.
- An authorized source can move through analysis, clip generation, validation and metadata drafting with auditable provenance.
- The owner receives a clear review queue with preview, rights, validation, channel target and metadata.
- A separately approved clip can be staged PRIVATE to the exact authenticated target channel(s), with verified video IDs and privacy states.
- No path can make a video Public without a separate final owner action.
- Errors, missing rights, uncertain ownership, failed verification or revoked scopes stop the pipeline and surface a concise owner action item.

## Status vocabulary

- `PLANNED`: recorded here; not implemented.
- `IMPLEMENTED`: code committed; tests not necessarily run.
- `TESTED`: named tests run with results.
- `CI_VERIFIED`: exact-head CI evidence recorded.
- `OWNER_ACCEPTED`: owner reviewed the behavior and explicitly accepted it.
- `BLOCKED`: security, rights, account connection or review dependency prevents execution.

