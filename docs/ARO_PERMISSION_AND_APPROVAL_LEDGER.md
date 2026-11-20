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

- 2026-11-20: ARO-CHAT-0022 / OpenAI GPT-6 received a bounded contributor scope from the owner's explicit EXECUTE NOW instruction: inspect the live repository, update its own chat reservation and factual handoff/governance records on the existing ARO-ZERO-ONE branch. No source-code implementation, merge, retarget, deployment, publishing, credential, destructive, or permission-management authority was granted.
- 2026-11-20: ARO-CHAT-0022 observed that GitHub reports push/admin capability for the connected credential. This is API capability only and does not expand the session's project authority.


- 2026-11-20: ARO-CHAT-0023 / OpenAI GPT-6 received a bounded QA/auditor scope from the owner's EXECUTE NOW instruction: inspect repository and exact-head CI evidence, review uploader/approval integration boundaries, and record a factual handoff. No application source, test, workflow, publishing, deployment, credential, destructive, merge, or permission-management authority was granted.
- 2026-11-20: ARO-CHAT-0023 observed GitHub API admin/push capability for the connected credential. This is technical capability only and does not expand this session's project authority.


- 2026-11-20: ARO-CHAT-0023 / OpenAI GPT-6 received a bounded contributor scope from the owner's explicit EXECUTE NOW instruction: inspect repository state, reuse the existing ARO-ZERO-ONE branch/PR, reserve its serial, and update factual audit/handoff records. No source-code implementation, merge, retarget, deployment, publishing, credential, destructive, or permission-management authority was granted.
- 2026-11-20: ARO-CHAT-0023 verified GitHub connector push/admin capability as an API property only. This does not confer owner authority.
- 2026-11-20: Issue #68 remains OPEN / UNASSIGNED; no owner grant assigning its implementation to this session was found. Implementation is NOT AUTHORIZED pending explicit owner assignment/approval.

- 2026-11-20: ARO-CHAT-0024 / OpenAI GPT-6 received a bounded QA/auditor scope from the owner's EXECUTE NOW instruction: inspect live repository state, reconcile chat serial collisions, review renderer/approval boundaries and exact-head CI evidence, and update factual audit/handoff records on the existing ARO-ZERO-ONE branch. No application implementation, merge, retarget, deployment, publishing, credential, destructive, or permission-management authority was granted.
- 2026-11-20: ARO-CHAT-0024 observed GitHub push/admin capability for the connected credential. This is technical capability only and does not expand the session's project authority.
- 2026-11-20: Issue #68 remains OPEN / UNASSIGNED. The issue body requires project-owner assignment/approval of the implementation owner; ARO-CHAT-0024 did not receive that specific implementation assignment, so uploader changes remain NOT AUTHORIZED.


- 2026-11-20 13:10 IST: ARO-CHAT-0025 / OpenAI GPT-6 received a bounded QA/auditor and documentation-contributor scope from the owner's explicit EXECUTE NOW instruction: inspect the existing ARO-ZERO-ONE repository state, reconcile CI/PR evidence, review renderer and uploader security boundaries, reserve its unique chat/task identity, and update canonical audit/handoff records on the existing workstream branch.
- ARO-CHAT-0025 did not receive authority to modify application/test/CI/publishing code, implement issue #68, merge or retarget PRs, deploy, publish, access credentials, perform destructive actions, or change permission grants. Issue #68 remains OPEN / UNASSIGNED pending explicit owner assignment/approval.
- GitHub connector admin/push capability was observed as technical API capability only; it does not expand this session's project authority.


## ARO-CHAT-0028 session grant and restrictions — 2026-11-20 13:14 IST

| Identity | Chat ID | Role | Granted scope | Granting authority / evidence | Status |
|---|---|---|---|---|---|
| OpenAI / GPT-6 session | ARO-CHAT-0028 | QA / AUDITOR; bounded documentation contributor | Read live repository/PR/issue/CI state; inspect canonical research/provider/Beta records; update this session's registry, handoff, dashboard, provider inventory, Beta status and analytics evidence on the existing ARO-ZERO-ONE branch | Owner's explicit EXECUTE NOW instruction in the current conversation; task ARO-GTA-P0-28 | ACTIVE FOR AUDIT AND DOCUMENTATION ONLY |

- This grant does not include application/test/workflow implementation, issue #68 assignment, merge, retarget, deployment, publishing, credential access, destructive operations, collaborator/permission changes, or owner approvals.
- GitHub API admin/push capability is technical capability only and does not expand project authority.
- ARO-CHAT-0027 is already reserved for the separate review-dashboard PR QA workstream; ARO-CHAT-0028 did not assume or override that assignment.
- Issue #68 remains OPEN / UNASSIGNED. Its implementation is NOT AUTHORIZED for this session unless the project owner explicitly assigns/approves the implementation owner.
- No owner-only action or permission escalation was performed by ARO-CHAT-0028.


## ARO-CHAT-0030 bounded session grant — 2026-11-20

| Identity | Chat ID | Role | Granted scope | Granting authority / evidence | Status |
|---|---|---|---|---|---|
| OpenAI / GPT-6 session | ARO-CHAT-0030 | CONTRIBUTOR | Implement the isolated P0-30 audio-stream validation change; add regression tests; update the Windows manual clipping wizard and usage documentation; update this session's canonical records; open a draft PR stacked on existing PR #66 | Project owner's explicit MASTER EXECUTION / EXECUTE NOW instruction in this conversation; PR #71 and branch `workstream/aro-chat-0030-audio-stream-acceptance-2026-11-20` | ACTIVE FOR ASSIGNED WORKSTREAM ONLY |

### Restrictions retained

- No merge, retarget, close, deployment, production publishing, public upload, credential access/change, destructive action, collaborator permission change, or permission escalation.
- Issue #68 uploader owner-identity integration remains outside this task and is NOT AUTHORIZED without its separately required explicit owner assignment/approval.
- GitHub API push/admin capability is technical capability only and does not confer owner authority.
- PR #71 remains draft and unmerged; owner review is required before integration.
- The registry reservation was recorded after the first implementation commits; this process deviation is disclosed in the registry and PR body.


## ARO-CHAT-0031 bounded session grant — 2026-11-20

| Identity | Chat ID | Role | Granted scope | Granting authority / evidence | Status |
|---|---|---|---|---|---|
| OpenAI / GPT-6 session | ARO-CHAT-0031 | CONTRIBUTOR / QA | Fix the isolated unclosed CSV reader in the existing batch-render test, add narrowly scoped coverage if needed, update canonical session records, and open a draft PR stacked on PR #71 | Project owner's master execution instruction in this conversation; task limited to P2 test hygiene | ACTIVE FOR ASSIGNED WORKSTREAM ONLY |

### Restrictions retained
- No merge, retarget, close, deployment, public upload, publishing, credential access, destructive action, or permission escalation.
- No uploader or issue #68 implementation; no application renderer changes.
- PR #71 remains draft/unmerged and is the explicit base dependency. Owner review remains required before integration.
- GitHub push/admin capability does not grant owner-only authority.


## ARO-CHAT-0032 bounded session grant — 2026-11-20

| Identity | Chat ID | Role | Granted scope | Granting authority / evidence | Status |
|---|---|---|---|---|---|
| OpenAI / GPT-6 session | ARO-CHAT-0032 | CONTRIBUTOR / QA | Isolated test-hygiene fix in `tests/test_batch_render.py`; canonical documentation/analytics correction after the ARO-CHAT-0031 concurrent reservation collision; draft PR only | Project owner's master execution instruction in this conversation; task ARO-GTA-P2-32 | ACTIVE FOR ASSIGNED WORKSTREAM ONLY |

### Restrictions retained
- No merge, retarget, deployment, upload, publishing, credential access, destructive action, or permission escalation.
- No uploader/issue #68 implementation or application renderer changes.
- PR #73 was closed unmerged as an invalid duplicate; new work is tracked separately under ARO-CHAT-0032.


### Serial-collision correction for the bounded permission ledger

- The provisional ARO-CHAT-0031 grant recorded earlier in this branch is INVALIDATED because concurrent PRs #72 and #74 already claim that serial.
- PR #73 was closed unmerged. Do not attribute its work or permission grant to the canonical ARO-CHAT-0031 identity.
- The test-hygiene contribution is now solely attributed to ARO-CHAT-0032 / ARO-GTA-P2-32, with the same bounded contributor restrictions above.


## ARO-CHAT-0033 bounded QA session grant — 2026-11-20

| Identity | Chat ID | Role | Granted scope | Granting authority / evidence | Status |
|---|---|---|---|---|---|
| OpenAI / GPT-6 session | ARO-CHAT-0033 | QA / AUDITOR; documentation contributor | Independently inspect PR #75 exact-head source and Ubuntu/Windows CI logs; verify the CSV-reader warning fix; record evidence in canonical docs and a documentation-only branch/PR | Project owner's master execution instruction in this conversation; task ARO-GTA-P2-33 | ACTIVE FOR BOUNDED QA AND DOCUMENTATION ONLY |

### Restrictions retained

- No merge, retarget, deployment, public upload, publishing, credential access, destructive action, permission escalation, or owner-only approval.
- No application, test, workflow, renderer or uploader implementation changes.
- PR #75 remains OPEN / DRAFT / UNMERGED; owner review is required before integration.
- Issue #68 remains outside this task and is not authorized without the owner's separate assignment/approval.
- GitHub connector admin/push capability does not grant owner-only project authority.
