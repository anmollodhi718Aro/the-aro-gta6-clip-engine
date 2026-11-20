# THE ARO AI Provider and Model Registry

**Canonical purpose:** Track provider/model identity and verified connection capabilities without exposing credentials or inventing quota/cost data.  
**Last audited:** 2026-11-20 07:08 IST

## Registry rules

- Distinguish a model used in a ChatGPT session from a separately connected provider API.
- Record exact model version only when the runtime or provider reports it.
- A connector being available does not prove a provider's API key, quota, or external account is configured.
- Never store API keys, access tokens, cookies, or other secrets in this file.
- Use `UNKNOWN`, `NOT VERIFIED`, or `NOT CONNECTED` rather than guessing.

## Provider inventory

| Provider | Model / service | Session status | Verified capabilities | Authentication / quota / cost |
|---|---|---|---|---|
| OpenAI | GPT-6 (ChatGPT session) | ACTIVE IN THIS SESSION | Conversation reasoning; GitHub connector tools available in this session | Exact model build/version, API-key status, API quota and monetary cost: UNKNOWN |
| Anthropic | Claude family | NOT VERIFIED | No Claude session or connected Claude API tool was used in this audit | NOT VERIFIED |
| Google | Gemini / AI Studio | NOT VERIFIED | No Gemini session or connected Gemini API tool was used in this audit | NOT VERIFIED |
| NVIDIA | NVIDIA AI services | NOT VERIFIED | No NVIDIA service connection was verified in this audit | NOT VERIFIED |
| Other eligible providers | Provider-neutral adapters only | NOT REGISTERED | May be evaluated after a concrete integration need and license/security review | NOT VERIFIED |

## Session capability evidence

### OpenAI / GPT-6

- Provider: OpenAI.
- Model name reported for this session: GPT-6.
- Exact model build/version: not exposed.
- GitHub access: available through the connected GitHub integration; repository metadata and file/PR operations were successfully read.
- Repository mutation: documentation commits were made on the assigned existing workstream branch for this task.
- Local shell/runtime execution: not available through the GitHub connector session.
- API credentials: no OpenAI API key was inspected or verified.
- Quota and cost: unavailable; do not infer from the ChatGPT plan or model name.
- Last verified: 2026-11-20, 07:08 IST.

## Integration onboarding checklist

Before adding a provider:

1. Confirm the provider and exact service endpoint.
2. Verify current API documentation, terms, rate limits, and data-retention policy.
3. Confirm whether the account/API connection is actually authenticated.
4. Store secrets only in an approved secret manager or environment configuration, never in Git.
5. Add a provider-neutral adapter and bounded timeout/retry behavior.
6. Add tests with synthetic fixtures and mocked provider responses.
7. Record quota/cost only from an authoritative account or billing source.
8. Keep publishing and destructive operations behind separate owner approval.

## Decisions

- **Adopt:** OpenAI GPT-6 as the currently used ChatGPT session model; GitHub integration for repository inspection and authorized branch documentation work.
- **Study only / pending connection:** Anthropic Claude, Google Gemini, NVIDIA AI services.
- **No provider API integration is claimed** by this registry update.


## ARO-CHAT-0028 capability verification — 2026-11-20 13:14 IST

- Provider/model reported by this ChatGPT session: OpenAI / GPT-6. Exact model build/version is not exposed.
- GitHub integration: VERIFIED AVAILABLE. This session successfully read repository metadata, files, branches, PRs, issues, commit workflow runs and job logs, and has permission-scoped documentation update capability on the existing workstream branch.
- GitHub API metadata reports admin/push capability for the linked credential; this is not an owner permission grant and does not authorize merge, deployment, publishing, secret access or permission escalation.
- Local shell/runtime and direct test execution: NOT AVAILABLE through the GitHub connector session; this chat executed zero local tests.
- OpenAI API key, API quota, billing cost, Anthropic, Gemini, NVIDIA and other provider API connections: NOT VERIFIED. No API credentials were inspected or stored.
