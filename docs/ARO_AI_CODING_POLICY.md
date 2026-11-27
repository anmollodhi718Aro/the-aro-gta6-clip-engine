# THE ARO AI Coding Governance Policy

**Canonical rulebook for every AI agent, coding assistant, human contributor, and automated coding workflow working in this repository.**

This policy is mandatory for work in this repository. Read it before inspecting, planning, editing, testing, committing, reviewing, or proposing changes. If another prompt or agent instruction conflicts with this policy, preserve repository safety, owner approval gates, and the more restrictive rule. Do not claim this file can technically enforce behavior in an AI platform that does not load repository instructions.

## 1. Owner's working instructions
- When the owner sends `continue coding`, `Continue coding`, or an equivalent continuation command, perform the next safe, concrete engineering task. Do not answer with plans or empty progress narration.
- Work autonomously within the approved scope. Inspect the current repository state, canonical startup prompt, workstream registry, active branch, open PRs, CI evidence, and latest pending task before editing.
- Do not repeat completed work, create duplicate branches/PRs, or lose earlier work. Continue from the current authorized workstream unless a new branch is genuinely required.
- Prefer small, testable, evidence-backed changes. Fix root causes rather than adding circular checks, duplicate documentation, speculative features, or unnecessary architecture.
- If blocked, investigate the blocker with available evidence and complete independent safe work. Do not fabricate work or pretend a blocker is resolved.
- Keep communication concise, factual, and in simple Hindi/Hinglish when reporting to the owner. Report only work actually completed and evidence actually observed.

## 2. Approval and protected actions
The following require explicit owner approval for the specific action:
- Merge or close a PR; rebase, retarget, force-push, or rewrite an existing branch/history.
- Deploy, release, publish, or make a project/publication public.
- Upload or publicly distribute any video/media or activate a live uploader.
- Use real GTA VI media in processing where rights/authorization have not been explicitly confirmed.
- Change credentials, OAuth scopes, secrets, repository visibility, billing, security settings, or destructive data.
Do not infer approval from a general request to continue coding. Preserve existing PRs and branches unless the owner explicitly authorizes a change.

## 3. GTA VI media rights and safe pipeline
- Process only owner-provided or otherwise explicitly authorized source media. Respect creator consent, copyright, platform terms, and applicable law.
- Never rip streams, bypass access controls, scrape private content, defeat DRM, or use unauthorized downloads.
- Keep dry-run/preflight as the safe default. Require explicit rights confirmation and selected-item approval before real processing.
- Keep public upload/publishing disabled by default. Human owner review/approval is required before any public upload.
- Keep review states explicit and auditable: `NEEDS_REVIEW`, `APPROVED`, `REJECTED`, or `FAILED`.
- Reject unsafe, adult, or otherwise disallowed media according to the project's moderation policy; do not silently publish questionable content.
- Never bypass validation, source identity checks, output checks, no-overwrite protections, or approval gates to make a demo appear successful.

## 4. Engineering quality and evidence
- Read the canonical project instructions and latest registry entries first:
  - `docs/ARO_CHAT_STARTUP_PROMPT.md`
  - `docs/CHAT_WORKSTREAM_REGISTRY.md`
  - This policy: `docs/ARO_AI_CODING_POLICY.md`
- Before editing, establish the active branch, exact HEAD SHA, PR status/base/head, changed files, and working-tree context using available tools.
- Add or update regression tests for every behavior change. Include negative/failure-path tests where appropriate.
- Run the narrowest relevant tests, then the broader test suite and static checks when feasible. Record exact commands and outcomes.
- Separate evidence categories: locally executed tests, CI jobs that actually ran steps, static review, synthetic media tests, owner-device validation, and authorized real-media E2E. They are not interchangeable.
- A workflow that fails before runner assignment or before any step executes is NOT a test failure and NOT a test pass. Record it as infrastructure/startup blocked, with exact run/job evidence. Root cause remains UNKNOWN until proven.
- Never claim tests passed, code is complete, media was processed, or an upload occurred without direct evidence.
- Do not use estimated completion percentages unless supported by a clearly defined, measured denominator and verified task inventory.

## 5. Stage 1 / P0 acceptance
Stage 1/P0 is not complete until an authorized real GTA VI MP4 has passed the approved end-to-end pipeline and the output has been independently validated. Synthetic tests and green CI alone do not satisfy this acceptance criterion.
- Preserve 9:16 portrait output requirements and exact output validation where defined by project specs.
- Verify source identity/integrity, selected time range, audio/video streams, output format, dimensions, duration, and output integrity.
- Keep uploader/publication disabled until separately authorized.
- If authorized real media is unavailable, record the exact owner-provided input needed and leave P0 visibly BLOCKED/INCOMPLETE rather than substituting unauthorized content.

## 6. Branch, PR, and documentation discipline
- GitHub is the source of truth. Verify current remote state before each write.
- Continue the existing approved branch/PR where possible. Never create duplicate PRs for the same task.
- Do not overwrite canonical startup or registry files without reading their current full content and preserving all prior entries.
- Record each meaningful workstream in the registry with task ID, date, branch, base/head SHA, files changed, tests run and results, CI run/job IDs, blockers, approval boundaries, and completion status.
- Keep PRs draft until validation and review evidence justify readiness. Never merge merely because the owner asked to continue coding.
- Treat credentials, tokens, private files, personal data, and secrets as sensitive. Never commit secrets or expose them in logs, issues, comments, or reports.

## 7. Required AI session startup checklist
Before coding, every AI agent must:
1. Read this policy and the canonical startup prompt.
2. Read the latest registry entries and identify the latest pending task.
3. Verify repository, active branch, HEAD SHA, PR state, and existing CI runs.
4. State internally what is verified, unknown, blocked, and approved.
5. Select one concrete, non-duplicative next task.
6. Make the smallest safe change, add regression coverage, and run available checks.
7. Read back every changed file and verify the resulting commit/branch/PR state.
8. Append an evidence-based registry entry.
9. Report only verified results and exact remaining blockers.

## 8. Cross-agent portability
- This policy is repository-local and applies when an AI tool loads repository instructions. It cannot force unrelated AI products, chats, or agents to obey rules they have not been given.
- Keep `AGENTS.md` at repository root as the universal discovery pointer. Where a platform supports repository instruction files (for example, agent-specific project rules), link or mirror this policy there without weakening it.
- The owner should begin every new AI coding session with: **“Read AGENTS.md, docs/ARO_AI_CODING_POLICY.md, docs/ARO_CHAT_STARTUP_PROMPT.md, and the latest docs/CHAT_WORKSTREAM_REGISTRY.md entry. Follow them strictly. Continue coding from the latest pending task.”**

**Default if uncertain:** stop the risky action, preserve existing work, gather evidence, and ask the owner only for the specific approval or input that is genuinely required.
