# Owner Actions and External Dependencies

The coding work should proceed without repeatedly asking the owner for routine decisions. These are the specific tasks that cannot be completed solely inside this repository.

## Needed before a real YouTube live-chat pilot

1. Choose a creator/source that has explicitly authorized chat analysis and clip preparation.
2. Obtain written permission that states the permitted scope (chat analysis, clipping, editing, distribution), duration, attribution, and any restrictions.
3. Create or use an eligible Google Cloud project, enable the relevant YouTube API, and complete the required OAuth setup.
4. Keep OAuth client secrets and refresh tokens private. Add secrets only through the appropriate secure provider settings when a deployment is configured. Never paste them into chat, issues, commits, or source files.
5. Provide a short local video file that the owner has the rights to process, or use a synthetic generated test video, for clip-render validation.
6. Confirm the video start time / stream clock mapping before using chat events to set video cut offsets.

## Needed before hosted/public use

- Select a hosting provider and region.
- Approve a spending ceiling for compute, bandwidth, AI, database, and storage.
- Decide retention periods and deletion expectations.
- Provide privacy policy, terms, support contact, and organization details required by the selected distribution channels.
- Complete age/account eligibility and platform requirements for any developer, billing, or store accounts.
- Review rights, privacy, security, and platform policy before a public pilot.

## Never send to the assistant or commit to GitHub

- passwords, passkeys, recovery codes
- OAuth client secrets or refresh tokens
- API keys
- payment card or bank details
- private identity documents

The assistant can write integration code and setup instructions. The account owner must perform consent, account authorization, billing, and legal approvals.
