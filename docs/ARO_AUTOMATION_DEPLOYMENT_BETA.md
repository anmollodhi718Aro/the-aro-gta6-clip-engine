# THE ARO Automation Deployment Beta

**Project tier:** Secondary / Beta  
**Priority:** P2, below THE ARO GTA 6 Clip Engine  
**Status:** PLANNED; implementation and deployment NOT VERIFIED  
**Last audited:** 2026-11-20 07:08 IST

## Purpose

A small, independently testable automation and deployment management experiment. It should register projects and workflows, track execution outcomes, retain logs, retry recoverable jobs, and require human approval for sensitive actions.

This is not an enterprise orchestration platform and must not delay the first authorized clip milestone.

## Repository and environment identity

| Item | Value | Status |
|---|---|---|
| Dedicated repository | Not identified in verified repository records | UNAVAILABLE |
| Deployment target | Not specified | UNAVAILABLE |
| Runtime / hosting provider | Not verified | UNAVAILABLE |
| Connected workflow provider | Not verified | NOT CONNECTED |
| Beta deployment | None verified | NOT DEPLOYED |
| Owner approval for production | Not granted | NOT AUTHORIZED |

Do not invent a repository URL or assume that the GTA 6 Clip Engine repository is also the Beta repository. Before implementation, search the owner's existing repositories and confirm the intended project with the owner.

## Beta MVP boundary

Start with one project and a small number of explicitly authorized workflows.

1. Project registration and metadata.
2. Workflow registration and version.
3. Trigger definition.
4. Execution ledger with queued/running/succeeded/failed/cancelled states.
5. Structured logs with secret redaction.
6. Bounded retry for transient failures only.
7. Dependency and prerequisite tracking.
8. Manual approval gates for privileged actions.
9. Small dashboard with real execution state.
10. Automated tests and a repeatable deployment guide.

## Execution safety

- Do not execute arbitrary repository code from untrusted sources.
- Do not store tokens, API keys, cookies, or secrets in workflow logs or Git.
- Use least-privilege service identities.
- Use bounded retries, idempotency keys, timeouts, and explicit failure states.
- A cancelled runner or dependency-install failure is not a test assertion failure.
- Do not retry non-idempotent or destructive operations automatically.
- Require owner approval before production deployment, permission changes, destructive actions, or external publication.

## Suggested initial data model

| Entity | Minimum fields |
|---|---|
| Project | project_id, name, repository, owner, status |
| Workflow | workflow_id, project_id, name, version, trigger, enabled |
| Execution | execution_id, workflow_id, status, started_at, ended_at, attempt, commit_sha |
| Log entry | execution_id, timestamp, level, message_redacted |
| Dependency | workflow_id, dependency_id, required_status |
| Approval | approval_id, execution_id, action, requested_by, decision, reviewer, reviewed_at |

Unknown values must remain null. Timestamps must include timezone information.

## Delivery phases

### Beta 0: identity and design
- Verify whether a separate repository already exists.
- Confirm the owner, target environment, and permitted workflows.
- Define threat model, secret handling, and audit retention.

### Beta 1: local execution ledger
- Implement the minimal schema and state transitions.
- Add unit tests for retries, cancellation, idempotency and approval gates.
- Run locally without external deployment.

### Beta 2: small dashboard
- Display registered workflows and real execution records.
- Show failure reasons and retry eligibility.
- Keep approval controls functional and auditable.

### Beta 3: controlled deployment
- Select a verified low-cost/free deployment target.
- Add health checks, rollback notes and owner-approved credentials.
- Deploy only after explicit owner approval.

## Shared concepts

The Beta may reuse documented concepts from the Clip Engine: chat serials, task ownership, permission ledger, approval records, CI evidence, and audit logs. Do not copy clipping business logic or tightly couple the two projects.

## Current blockers and next action

- **Blocker:** No separate Beta repository or deployment target was verified in this audit.
- **Next action:** Verify the existing repository identity and confirm whether the owner wants the Beta workstream opened after the first authorized clip is produced.
- **Current decision:** Keep this project planned and isolated. P0 clipping work takes precedence.
