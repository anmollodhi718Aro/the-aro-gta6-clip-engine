# Security and Data Retention

## Secrets

- Never commit API keys, OAuth tokens, passwords, private keys, or production credentials.
- Keep a safe `.env.example` with placeholder names only.
- Use environment variables locally and a suitable secrets manager in hosted environments.
- Redact secrets from logs and error reports.
- Rotate credentials after suspected exposure.

## Access control

Future services should use least-privilege roles:
- owner/admin: configure sources, permissions, and service settings
- editor: review and export approved clips
- viewer: read-only access

Require server-side authorization checks for every protected action. Do not trust client-side UI state.

## Data minimization

- Store source identifiers, event summaries, candidate timestamps, and review decisions only as needed.
- Avoid retaining full chat text or personal data unless necessary and permitted.
- Define retention periods before enabling persistent collection.
- Provide a process to delete account data and source-derived data where required.
- Document backups and the maximum time before deleted data ages out of backups.

## Operational safeguards

- rate limits and bounded retries
- audit trail for permission changes, approvals, exports, and administrative actions
- encryption in transit and at rest where supported
- dependency and vulnerability checks
- backups with restore tests
- incident response and emergency stop procedure

## AI-assisted maintenance

Diagnostics and bounded retries may run automatically. Proposed code changes must be made on an isolated branch, with tests and a reviewable diff. Production merges, releases, secret changes, and deployment require explicit owner approval.
