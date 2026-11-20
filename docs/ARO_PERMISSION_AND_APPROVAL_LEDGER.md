# THE ARO Permission and Approval Ledger

**Canonical purpose:** Record project authority, contributor roles, granted scopes, restrictions, and owner approvals.  
**Last audited:** 2026-11-20 07:08 IST  
**Source of truth:** Explicit owner instructions plus verified repository records. A GitHub API capability is not itself a project permission grant.

## Authority

- **Project owner:** THE ARO. The repository owner account is `anmollodhi718Aro`.
- **Final authority:** The project owner retains control over merges, production deployment, public uploads, sensitive permission changes, production credentials, destructive actions, and major architecture decisions.
- **No delegated project lead or maintainer:** No separate grant was verified in the records inspected for this update.

## Roles

| Role | Permitted scope | Explicit restrictions |
|---|---|---|
| OWNER | All project decisions and owner-only approvals | None within the project authority model |
| PROJECT LEAD | Coordinate assigned workstreams and recommend integration | Cannot override owner-only approvals |
| MAINTAINER | Review and maintain approved branches/docs within a granted scope | No implied merge, deployment, or publishing authority |
| CONTRIBUTOR | Implement assigned tasks in an isolated or explicitly assigned workstream | No merge, deployment, publishing, secret access, or destructive actions unless separately approved |
| QA / AUDITOR | Inspect, test where tooling permits, and report evidence | No code promotion or production action by default |
| READ-ONLY RESEARCHER | Inspect permitted project and public reference material | No repository mutation |

## Session grants and observed capabilities

| Identity | Chat ID | Role | Granted scope | Granting authority / evidence | Status |
|---|---|---|---|---|---|
| OpenAI / GPT-6 session | ARO-CHAT-0020 | CONTRIBUTOR | Read repository state; create the four assigned governance/dashboard documents on the existing ARO-ZERO-ONE branch; update this session's attribution records | Owner's explicit “EXECUTE NOW” instruction in the current conversation; task ARO-GTA-P0-20 | ACTIVE FOR ASSIGNED DOCS ONLY |

### Capability is not authority

The GitHub repository metadata endpoint reported `admin=true` for the connected GitHub credential. This describes the credential's API capability. It does **not** grant this AI session owner authority or permission to merge, deploy, publish, change repository security settings, or access production secrets.

## Owner-only actions

The following remain **NOT AUTHORIZED** unless a separate, explicit owner approval is recorded for the exact action:

- Merge any pull request or change the default branch.
- Retarget or close an existing pull request.
- Deploy to production or change production infrastructure.
- Upload or publish any clip publicly.
- Access, reveal, rotate, or change production credentials.
- Change collaborator permissions or grant permission escalation.
- Delete branches, files, data, or other project resources destructively.
- Approve a clip for publication on behalf of the owner.

## Media and publishing approvals

Creator/source permission and destination-channel publishing permission are independent:

1. Source acquisition requires a matching, active creator grant with the required read scope.
2. Public upload requires an explicit per-clip owner decision and a separate active `publish` scope for the destination channel.
3. A provider media reference or chat metadata does not prove that authorized video bytes were acquired.
4. Unreviewed or rejected clips must not pass the publishing gate.

## Approval record format

Record each future grant with: identity, provider, chat ID, role, project, exact scopes, restrictions, granting authority, evidence URL or commit, start time, expiry, and revocation status. Do not infer missing fields.

## Audit history

- 2026-11-20: ARO-CHAT-0020 received a bounded documentation-contributor assignment through the owner's execute instruction. No merge, deployment, publishing, credential, or destructive permission was granted.
- 2026-11-20: Repository metadata reported admin API capability for the connected GitHub credential; this is recorded as an observed capability only, not as an AI authority grant.
- No production deployment, public upload, or owner-only approval was performed by this session.
