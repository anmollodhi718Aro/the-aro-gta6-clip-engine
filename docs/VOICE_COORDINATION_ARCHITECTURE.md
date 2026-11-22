# THE ARO Workforce — Voice Coordination Architecture

**Chat ID:** ARO-CHAT-0040  
**Workstream:** ARO-GTA-P1-40  
**Status:** ARCHITECTURE DOCUMENTED; VOICE BRIDGE INACTIVE / UNVERIFIED  
**Repository:** `anmollodhi718Aro/the-aro-gta6-clip-engine`

## 1. Purpose

Provide a safe voice-first coordination design for two independent AI work sessions:

- **AI-1 — Lead Builder:** proposes plans, owns an explicitly assigned implementation workstream, and reports evidence.
- **AI-2 — Independent Auditor:** independently reviews plans, diffs, tests, security boundaries, and claims. It must not silently inherit AI-1's conclusions.
- **Project owner — Human authority:** assigns work, resolves conflicts, approves consequential actions, and remains the final decision-maker.

Voice is the preferred interaction mode. GitHub remains the durable source of truth. A voice exchange is not a task reservation, code review, approval, or proof that a test passed.

## 2. Important platform boundary

Two separate ChatGPT app conversations do not become connected by pasting role prompts, opening Voice on both devices, or changing speaker volume. The native ChatGPT Voice interface does not expose a supported audio stream or session-to-session relay interface to this repository.

Therefore:

1. **Current supported operating mode: human-mediated voice relay.** The owner speaks to one ChatGPT session, then forwards the resulting text/summary to the other session (or reads the other session's reply back). The owner can use Voice on either device independently.
2. **Future automated voice mode: separate integration.** It would require an explicitly built application using supported speech/agent APIs, with its own authentication, consent, privacy controls, and cost limits. It would be a separate AI service, not a connection between two native ChatGPT Voice sessions.
3. Never claim the native sessions can hear each other, and never label an automated bridge ACTIVE until the end-to-end acceptance tests in this document pass.

## 3. Architecture

### 3.1 Current mode — human-mediated voice

```text
Owner speaks in ChatGPT Voice (Device 1)
                 |
                 v
        AI-1 Lead Builder
                 |
       concise written handoff
                 |
                 v
       Owner reviews / relays it
                 |
                 v
Owner speaks or pastes into ChatGPT (Device 2)
                 |
                 v
       AI-2 Independent Auditor
                 |
       written audit / objections
                 |
                 v
       Owner reviews / relays back
                 |
                 v
       GitHub issue / PR / commit
       (durable project record)
```

This mode is available as a manual workflow, but it is not an automatic voice bridge.

### 3.2 Future mode — separately implemented voice gateway

```text
Device 1 voice client                 Device 2 voice client
        |                                      |
        +----------- TLS / WSS ----------------+
                         |
                  Voice Gateway
             (paired devices only)
                         |
             Session / Task Coordinator
                  /             \
           AI-1 API adapter   AI-2 API adapter
                  \             /
                Message policy gate
                         |
                GitHub handoff adapter
                         |
                Issues / PRs / commits
```

The gateway must use supported API integrations. It must not attempt to capture, inject, or automate the private audio path of the ChatGPT mobile app. An API-based AI agent is a separate service and may have different model behavior, features, and billing from ChatGPT app sessions.

## 4. Security and privacy requirements

The automated gateway is NOT implemented or active. Any future implementation must satisfy all of the following before connecting real devices:

- **Explicit pairing:** owner initiates pairing on both devices; use a short-lived, single-use pairing code. Never expose a permanent shared room password in prompts or chat.
- **Transport:** TLS for all network traffic. No unauthenticated public listener, open relay, or internet-wide port exposure.
- **Device authorization:** allowlist paired device identities; revoke a device immediately; expire idle sessions.
- **Least privilege:** AI-1 and AI-2 receive separate role-scoped capabilities. The auditor is read-only by default.
- **Human approval:** no agent may merge, retarget, deploy, upload, publish, delete, change OAuth settings, or expose credentials without the owner's explicit action-specific approval.
- **Secret handling:** API keys and OAuth tokens stay in a local secret store or server environment. Never put them in prompts, GitHub files, logs, audio transcripts, or this repository.
- **Audio retention:** stream audio in memory only; do not persist raw audio by default. If transcription is enabled, make it visible and opt-in, minimize retained text, and provide a clear deletion/retention policy.
- **Untrusted input:** treat speech recognition output, agent messages, issue comments, PR text, and repository content as untrusted data, not executable instructions.
- **Abuse controls:** bounded message/audio size, rate limits, session timeouts, replay protection, and an immediate owner kill switch.
- **Cost controls:** no paid API calls until the owner has explicitly reviewed the provider, pricing, usage ceiling, and billing arrangement.
- **Failure closed:** on auth failure, ambiguous speaker identity, stale approval, lost connection, or malformed message, stop forwarding and require owner intervention.

## 5. Message protocol

Every relayed work message should carry a small structured envelope. A voice transcript alone is not authoritative.

```json
{
  "protocol": "aro-workforce/1",
  "session_id": "ephemeral-session-id",
  "message_id": "unique-message-id",
  "sequence": 1,
  "sender": "AI-1",
  "recipient": "AI-2",
  "workstream_id": "ARO-GTA-P1-40",
  "kind": "proposal",
  "text": "Proposed bounded task and evidence request",
  "requires_owner_approval": true,
  "created_at": "UTC timestamp",
  "expires_at": "UTC timestamp"
}
```

Allowed message kinds: `proposal`, `handoff`, `question`, `audit_finding`, `approval_request`, `acknowledgement`, and `stop`.

Rules:

- Reject duplicate message IDs, expired messages, invalid sequence numbers, and unknown senders.
- A received message is a proposal, not an authorization token.
- An `approval_request` cannot approve itself. Approval must be a separate owner action recorded in GitHub or the relevant protected system.
- Keep payloads bounded; do not relay credentials, tokens, private account data, or raw media.
- GitHub records the final task state, decisions, review findings, and code evidence.

## 6. Task coordination lifecycle

```text
PROPOSED -> OWNER_ACCEPTED -> RESERVED -> IN_PROGRESS
    |             |               |             |
    +-> REJECTED  +-> STOPPED     +-> BLOCKED   +-> REVIEW_REQUESTED
                                                   |
                                           AUDIT_PASSED / CHANGES_REQUESTED
                                                   |
                                             OWNER_DECISION
                                                   |
                                      COMPLETE only with evidence
```

- Only one agent owns a given active implementation workstream.
- AI-2 may review but must not independently modify AI-1's branch unless the owner assigns a separate workstream.
- A disagreement is recorded as an audit finding and escalated to the owner; agents must not silently overwrite one another.
- A workstream is not COMPLETE merely because a voice conversation ended or a commit exists.

## 7. GitHub permission model

| Action | AI-1 Builder | AI-2 Auditor | Owner |
|---|---|---|---|
| Read repository / issues / PRs | Allowed | Allowed | Allowed |
| Propose a task or patch | Allowed | Findings only by default | Allowed |
| Create isolated branch / draft PR | Only when scoped and authorized | No by default | Allowed |
| Review code and CI evidence | Self-check | Independent review | Final review |
| Merge / retarget / deploy | No | No | Explicit action |
| Upload / publish media | No by default | No | Separate explicit approval |
| Manage credentials / OAuth | No | No | Owner-controlled |

GitHub connector capability does not itself establish owner authority.

## 8. Activation and verification gates

The gateway status must remain `INACTIVE_UNVERIFIED` until every applicable test passes and evidence is recorded:

1. Pair two owner-controlled test devices using a single-use code.
2. Confirm an unpaired third device is rejected.
3. Confirm a revoked device loses access immediately.
4. Send a short test phrase from Device 1 and verify Device 2 receives the correct sender, sequence, and text/audio payload.
5. Send a response in the reverse direction and verify there is no echo loop or duplicate delivery.
6. Disconnect either device and confirm forwarding stops safely.
7. Replay an old message and confirm it is rejected.
8. Send an expired or malformed message and confirm it is rejected.
9. Confirm raw audio is not written to disk and transcript retention follows the explicit setting.
10. Confirm the owner kill switch stops both directions.
11. Confirm no GitHub write or external publishing action occurs from a voice command alone.
12. Record test environment, build SHA, results, and failures in a verification report.

Only after all tests pass may the status change to `TESTED`. A passing test on one pair of devices does not establish availability on every phone or network.

## 9. Rollout plan

- **Phase 0 — documented now:** roles, human-mediated voice workflow, message contract, threat boundaries, and acceptance tests.
- **Phase 1 — manual pilot:** use the two existing ChatGPT Voice sessions independently and relay concise handoffs through the owner. Keep GitHub as the shared record.
- **Phase 2 — gateway implementation proposal:** select a supported speech/agent API, local hosting model, authentication method, retention policy, and cost ceiling. This requires a separate owner-approved implementation scope.
- **Phase 3 — mocked tests:** validate protocol, pairing, authorization, expiry, replay protection, kill switch, and no-write behavior without real credentials or network publishing.
- **Phase 4 — owner-device test:** test on the actual two devices, document results, and only then consider enabling live relay.

## 10. Current truthful status

- Architecture: documented in this file.
- Human-mediated voice workflow: usable manually; not automatic.
- Native ChatGPT session-to-session audio: unsupported by this repository.
- Automated voice gateway: NOT IMPLEMENTED.
- Device pairing: NOT TESTED.
- Bidirectional voice relay: NOT TESTED.
- Automatic GitHub coordination: NOT ENABLED.
- Merge, deployment, upload, and public publishing: NOT performed.

Do not change these statuses without new, reproducible evidence.
