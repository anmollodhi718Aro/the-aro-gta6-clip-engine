# ARO-CHAT-0315 — render exception output inspection requirement

- Workstream: ARO-GTA-P1-315
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Existing PR: #386
- Existing branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`

## Finding

Static review found that `render_clip()` can atomically link a completed output to its final destination and then raise during temporary staging-directory cleanup. The caller's prior generic failure report did not explicitly state that the destination might already exist or require inspection before retry.

## Change

- Catch ordinary exceptions at the render-helper call boundary.
- Return FAIL while preserving the configured output path.
- Keep `processing_started` unknown because the helper did not return successfully.
- Set `output_inspection_required=true` and explicitly warn against retry until the output is inspected.
- Do not automatically delete or overwrite a possible output.
- Add a mocked regression that creates the destination and then raises a cleanup exception.

## Validation

- Regression added: `test_render_exception_preserves_possible_output_and_requires_inspection`.
- Local repository tests NOT RUN in this connector session.
- Latest observed Actions failure on prior head had runner_id=0, no runner name, and zero steps; this is not evidence of a test failure.
- New exact-head CI PENDING / NOT VERIFIED; independent review NOT RECORDED.
- Owner-device Windows verification NOT VERIFIED; authorized real MP4 NOT PROCESSED.

## Safety

- PR #386 remains OPEN / DRAFT / UNMERGED with its existing base and ancestry.
- No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
