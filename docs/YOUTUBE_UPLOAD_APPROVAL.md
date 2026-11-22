# YouTube upload approval gate

This CLI is intentionally dry-run-first. It does not scrape streams or download platform video. The input video must be a local asset that the operator owns or is authorized to use.

## Approval model

An upload requires all of the following:

1. A local rights preflight report with no blocking errors, followed by explicit `--confirm-rights` at upload time.
2. A current source permission JSON record granting the `publish` scope.
3. An immutable per-clip approval JSON record bound to the exact `clip_id` and `source_id`.
4. An OAuth session that resolves through YouTube Data API `channels.list(mine=True)` to exactly one channel, matching the configured `--channel-id`.
5. A valid HMAC signature on the approval record, using a protected `ARO_UPLOAD_APPROVAL_KEY` environment variable of at least 32 bytes.
6. A deliberate `--upload` invocation.

The reviewer subject is populated from the OAuth-resolved channel ID. No reviewer ID is accepted from a CLI argument. The approval record is re-read and verified, and the permission grant is re-checked immediately before the YouTube upload request. Expired, revoked, mismatched, missing, or modified records fail closed.

The approval file is created exclusively and cannot be overwritten. A changed decision requires a new record path and an explicit owner review. Keep both the signing key and OAuth token outside Git, restrict access to them, and back up the signing key securely. Anyone who obtains the signing key can create valid local approval records; HMAC is integrity protection, not a substitute for secure key custody or a server-side approval service.

## Local setup

Provision a unique random key in a password manager or secret manager, then expose it to the process as `ARO_UPLOAD_APPROVAL_KEY`. Do not paste the key into source files, issue comments, chat logs, or Git.

The OAuth Desktop client and token remain local. The OAuth flow requests YouTube upload and read-only scopes so the authenticated destination channel can be verified. Existing tokens without the read-only grant may need to be re-authorized.

A source permission record has this shape:

```json
{
  "source_id": "creator-or-source-id",
  "granted_by": "creator-owner-subject",
  "scopes": ["read_live_stream", "publish"],
  "granted_at": "2026-11-22T00:00:00+00:00",
  "expires_at": null,
  "revoked_at": null
}
```

## Two-step owner review and upload

First, run the CLI with `--record-approval`, the exact clip/source IDs, configured channel ID, approval path and permission path. The CLI authenticates through OAuth, verifies the destination channel and active publish grant, then asks the owner to type `APPROVE`. This step records approval only; it never uploads.

After reviewing the final local video and rights report, run a separate invocation with `--upload --confirm-rights` and the same clip/source/channel and record paths. The upload is attempted only after all gates pass.

For safety, this documentation does not include real credentials, tokens, signing keys, or a live upload command. Unit tests must mock provider clients and must never perform a network upload. Public, unlisted and private uploads all require the explicit owner approval record and active publish permission.
