# ARO-CHAT-0304 — Reserve the run report before candidate media hashing

- Chat ID: ARO-CHAT-0304
- Workstream ID: ARO-GTA-P1-304
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Existing PR: #386
- Existing branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Scope: one bounded CLI ordering correction; no new branch or PR.

## Finding

Candidate-CSV mode computed the selected media SHA-256 before reserving the exclusive run report. Hashing reads the entire selected video and can be expensive. If report creation later failed or collided with an existing path, the CLI had already read the media without leaving the durable RUNNING record that the operator relies on to distinguish an interrupted or attempted run.

## Change

- Keep CSV row, source-ID, and trusted-digest-format validation before report reservation because these operations inspect only selection metadata and arguments.
- Move selected media SHA-256 verification until after the exclusive RUNNING report is written, flushed, and fsynced.
- Record source-hash open/read errors and trusted-digest mismatches as terminal FAIL reports.
- Do not invoke the renderer after candidate source verification fails.
- Add a regression that checks the report is parseable and has status RUNNING from inside the source-hash callback.
- Retain the verified digest in terminal candidate-selection metadata after a successful comparison.

## Commits

- Production: `3204190a41814b73b26859b48d55a2f74d71df80`
- Regression: `efda642d6f0ae5a2168606fa9dce7a27839bff5b`
- Operator documentation: `5c6de71a4f7fd7693c65a48d6a12f445249be04e`

## Validation

- Local repository tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED; inspect naturally triggered runs only.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Real authorized MP4: NOT PROCESSED / NOT VERIFIED.
- Synthetic/mock regression added but not executed in this session.

## Safety and scope

- Existing PR #386 remains OPEN / DRAFT / UNMERGED.
- Preserve its existing base and ancestry; no merge, rebase, retarget, or integration.
- No workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, or deployment.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Live uploads and public publishing remain disabled.
