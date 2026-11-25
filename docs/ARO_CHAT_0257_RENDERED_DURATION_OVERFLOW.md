# ARO-CHAT-0257 | Reject Unrepresentable Rendered Duration Metadata

- Exact chat title: `ARO-CHAT-0257 | Reject Unrepresentable Rendered Duration`
- Workstream: `ARO-GTA-P1-257`
- Parent pipeline: PR #386 / ARO-GTA-P1-244
- Existing branch preserved: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- No duplicate PR, branch, or ancestry change.

## Finding

Static review found that the post-render FFprobe duration validation called `math.isfinite()` without an exception boundary. An extremely large integer can raise `OverflowError`, escaping the renderer instead of returning the required fail-closed report.

## Change

- Validate the post-render duration inside a narrow exception boundary.
- Treat `OverflowError`, `TypeError`, and `ValueError` as invalid metadata.
- Return the existing deterministic rendered-duration FAIL report.
- Add a regression using an enormous integer duration returned by the mocked post-render FFprobe result.
- Preserve the dry-run, explicit rights confirmation, no-overwrite, one-selected-video, and no-upload/no-publishing gates.

## Commits

- Production: `7456890f0563cf69b7d843b784bbfcf8c12fa59d`
- Regression test: `01e308f77423809eb35897c60ddef78fde55f8d3`
- Operator docs: `a487fa3fa4ea13cafdbfa3f9cf2f38f62ab955d1`

## Validation

- Static finding and patch recorded.
- Repository unit tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Real authorized media: NOT PROCESSED / NOT VERIFIED.

## Safety and integration

- PR #386 remains DRAFT / OPEN / UNMERGED.
- Existing #383 -> #380/#379 ancestry is preserved. The live parent branch has advanced; compare reports divergence. Do not rebase, retarget, merge, or integrate without explicit owner approval.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
- No workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, merge, rebase, retarget, or deployment occurred.
