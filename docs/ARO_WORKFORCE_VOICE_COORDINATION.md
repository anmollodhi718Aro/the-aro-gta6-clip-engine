# THE ARO Workforce Voice Coordination Architecture

**Status:** DESIGN IMPLEMENTED IN DOCUMENTATION; runtime NOT IMPLEMENTED; voice NOT ACTIVE; automatic coordination NOT VERIFIED  
**Workstream:** ARO-VOICE-0040  
**Owner control:** Human owner remains the final authority for privileged actions.

## 1. Purpose and non-goals

Provide a safe voice-first coordination path for two independent engineering agents:

- **AI-1 / Lead Architect:** decomposes approved work, proposes changes, reports implementation evidence, and publishes handoffs.
- **AI-2 / Independent Auditor:** independently reviews task scope, diffs, tests, security boundaries, and claims. It does not inherit AI-1's conclusions as evidence.
- **Human owner:** starts/stops sessions, grants task-specific permissions, resolves conflicts, and approves privileged actions.

This architecture does not connect two ChatGPT mobile Voice sessions directly. ChatGPT app sessions do not become mutually addressable merely because both devices have microphones and speakers. The production design therefore uses separately authenticated agent runtimes behind a coordination service. ChatGPT Voice may remain a human-facing interface, but it is not treated as the machine-to-machine transport.

Non-goals: autonomous merge, deployment, publishing, credential handling by a voice model, always-on recording, unrestricted shell access, or uncontrolled agent-to-agent loops.

## 2. High-level topology

```text
Owner phone / tablet
  - Push-to-talk control
  - Visible active-speaker indicator
  - Stop / mute / revoke controls
  - Spoken status and confirmation
          |
          | authenticated WebRTC audio + HTTPS control
          v
Voice Gateway (backend only)
  - session authentication and role binding
  - speech-to-text for owner commands
  - text-to-speech for agent messages
  - bounded turn-taking / speaker queue
  - transcript redaction and retention policy
          |
          v
Coordination API + durable task/event store
  - task IDs, lease/expiry, idempotency
  - append-only event/audit trail
  - explicit approval state machine
  - rate limits, quotas, stop switch
       /                              \
      v                                v
AI-1 Agent Runtime                 AI-2 Agent Runtime
Lead Architect                     Independent Auditor
separate identity                  separate identity
least-privilege tools              read-first / review tools
      |                                |
      +---------------+----------------+
                      |
               GitHub adapter
          scoped branch / PR / checks
                      |
             Human owner approval
```

The gateway transports bounded messages; it does not grant repository permissions. Agent runtimes authenticate independently. The GitHub adapter enforces its own least-privilege authorization and never accepts a voice transcript as sufficient authorization for a privileged operation.

## 3. Voice interaction model

1. Owner explicitly starts a named session and presses **Talk** to send a command.
2. Gateway transcribes the command and displays the transcript for correction when confidence is low or the command is consequential.
3. The coordination service creates a typed task event. AI-1 receives only its assigned task and allowed tools.
4. AI-1 sends a concise text result plus structured evidence. TTS reads the result to the owner.
5. AI-2 is invoked as a separate review task. It receives the task specification and relevant immutable GitHub references, not AI-1's hidden reasoning.
6. AI-2 returns independent findings. TTS reads the review after AI-1's turn ends.
7. The owner may ask follow-up questions using push-to-talk. No always-open microphone is required.

**Turn-taking:** one active speaker at a time. Use an explicit queue, a short audible speaker label, interruption support for the owner, and a hard maximum turn duration. Never pipe device speaker output back into another device microphone as the coordination mechanism.

**Fallback:** if speech recognition, TTS, WebRTC, or the gateway fails, fall back to a visible text handoff in the shared task record / GitHub. Failure must not silently drop a task or mark it complete.

## 4. Message contract

Every event must include:

- `event_id`: globally unique idempotency key
- `session_id`: short-lived coordination session
- `task_id`: owner-approved bounded task
- `sender_role`: `OWNER`, `LEAD`, `AUDITOR`, or `SYSTEM`
- `recipient_role`: explicit recipient
- `created_at` and `expires_at`: server timestamps
- `message_type`: `TASK`, `STATUS`, `HANDOFF`, `REVIEW`, `APPROVAL_REQUEST`, or `STOP`
- `body`: bounded plain text; no credentials or hidden prompt content
- `evidence_refs`: immutable commit, PR, check-run, or artifact references where applicable
- `approval_ref`: optional server-issued approval record; never a user-supplied boolean

Reject unknown roles, expired sessions, expired tasks, oversized payloads, duplicate event IDs with conflicting bodies, and messages that lack an authorized task scope. Treat all agent and repository content as untrusted data, not executable instructions.

## 5. Trust, authorization, and fail-closed rules

- Owner authentication is separate from agent authentication. Use short-lived, revocable session credentials; keep secrets server-side.
- Bind each agent identity to one role. Do not let AI-1 impersonate AI-2 or issue an auditor approval.
- Default AI-2 to read-only repository access. Any write scope must be separately granted for a named branch and bounded task.
- Enforce task leases, rate limits, message-size limits, maximum agent turns, and loop detection.
- A voice transcript is a request, not proof of identity or authorization. Consequential owner commands require an authenticated confirmation step in the UI.
- Never speak, display, store, or commit access tokens, passwords, private keys, OAuth refresh tokens, or recovery codes. Redact secrets before logging or TTS.
- Treat prompt injection in repository files, PR descriptions, comments, media metadata, and transcripts as untrusted input.
- No voice-only approval for merge, release, deployment, upload, publishing, permission changes, credential access, or destructive operations. Require a separate authenticated confirmation bound to the exact action, target, and current state.
- If the owner identity, channel identity, approval record, permission scope, or evidence is uncertain, deny the action and request human review.
- The global stop switch immediately blocks new agent tasks, cancels queued speech, revokes the active session, and records a stop event.

## 6. GitHub workflow boundaries

- AI-1 may prepare changes only on its allocated workstream branch and within the task's declared file/scope boundary.
- AI-2 reviews the exact head SHA and exact CI run; it must not approve based on a stale branch tip or a summary alone.
- Agents may create draft PRs only when the task grant explicitly includes that action.
- Merge, base retargeting, release, deployment, public upload, and publishing remain owner-controlled and require action-specific confirmation.
- The existing issue #68 authenticated channel-owner approval gate remains independent. Voice coordination cannot satisfy or bypass it.
- Keep the clip engine's rights/consent requirements intact. Permission to process media does not imply permission to publish it.

## 7. Privacy and operational safeguards

- Default to push-to-talk; no background capture.
- Do not retain raw audio by default. If audio retention is later required, obtain explicit opt-in and define purpose, duration, access, and deletion behavior first.
- Retain only the minimum redacted transcript and structured event metadata needed for audit; define a short configurable retention window.
- Encrypt transport and stored task records; restrict logs to authorized operators.
- Provide visible mic, recording, connection, active-agent, and active-speaker indicators.
- Provide mute, disconnect, session revoke, and global stop controls.
- Do not expose internal chain-of-thought. Handoffs contain concise conclusions, changed paths, exact SHAs, test evidence, risks, and open questions.

## 8. Suggested implementation sequence

1. **Protocol and threat model:** define schemas, role claims, session lifecycle, approval state machine, and threat tests.
2. **Text-only coordination MVP:** authenticated task queue, durable event log, idempotency, role separation, stop switch, and GitHub reference handoffs.
3. **Voice gateway:** push-to-talk WebRTC, speech-to-text, text-to-speech, explicit turn-taking, and text fallback.
4. **Agent adapters:** independently authenticated Lead and Auditor runtimes with provider-neutral interfaces and scoped tools.
5. **GitHub adapter:** branch/PR/check read and bounded draft-PR write actions; privileged actions denied by default.
6. **Security and reliability tests:** auth failures, replay, expiry, role spoofing, prompt injection, secret redaction, queue flooding, loop detection, disconnect, stop-switch, and fail-closed approval.
7. **Owner pilot:** two devices, test repository or non-production branch, no real publishing credentials, owner-supervised session.
8. **Activation gate:** publish a verification report with exact commit, environment, test results, and owner acceptance. Until then the status remains NOT ACTIVE / NOT VERIFIED.

## 9. Acceptance tests required before activation

- Two distinct agent identities cannot impersonate one another.
- Owner authentication and task authorization are checked server-side on every consequential action.
- Replayed, expired, duplicate-conflicting, malformed, or over-limit events are rejected.
- AI-2 can independently inspect the exact PR head but cannot write or approve a privileged action by default.
- Agent-to-agent turns are bounded and loop detection stops runaway exchanges.
- Push-to-talk works without always-on microphone capture; mute and stop take effect immediately.
- Speaker output is never used as an implicit microphone command.
- TTS output matches the approved text; secret-redaction tests pass before synthesis.
- Disconnects preserve the last durable event and resume without duplicate task execution.
- Voice outage falls back to text and never changes task/approval state.
- Merge, deployment, upload, publishing, credential access, and destructive operations remain denied without separate authenticated owner approval.
- An owner-supervised two-device pilot passes and is documented before status changes to ACTIVE.

## 10. Current status

| Capability | Status |
|---|---|
| Voice-first architecture and trust boundaries | DOCUMENTED |
| Text coordination service | NOT IMPLEMENTED |
| Voice gateway / WebRTC | NOT IMPLEMENTED |
| Speech-to-text / text-to-speech adapters | NOT IMPLEMENTED |
| Independent agent runtimes | NOT IMPLEMENTED |
| GitHub scoped adapter | NOT IMPLEMENTED by this workstream |
| Two-device end-to-end test | NOT RUN |
| Automatic coordination | NOT ACTIVE / NOT VERIFIED |
| Voice communication | NOT ACTIVE / NOT VERIFIED |

**Activation rule:** documentation, a branch, a PR, or a successful unit test is not proof that voice communication works. Only a successful owner-supervised end-to-end test across two devices can change the voice status.
