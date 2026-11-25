# ARO-CHAT-0261 | Exact-Head CI and Single-Clip Source Audit

- Workstream: `ARO-GTA-P1-261`
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Continuation branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Existing PR: [#386](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/386), OPEN / DRAFT / UNMERGED
- Starting head at reservation: `5fd9100218fd8d8abb5c8e4e43e03f31a0f2ba9a`
- Current audited PR head: `1ae6da85595086880caf7b47eae962df0151264f`
- Current base: `workstream/aro-chat-0243-single-video-preflight-schema-guard-2026-11-25` at `e6dffa5dabdd81f401f6189957c632fd49aad4bc`
- Audit date: 2026-11-25

## Exact-head CI and PR state

- Commit-associated PR workflow lookup for exact head `1ae6da85595086880caf7b47eae962df0151264f` returned zero workflow runs.
- Combined commit status for that exact SHA is `pending` with zero status entries. This is absence of check evidence, not a pass and not proof of a code failure.
- PR #386 is OPEN / DRAFT / UNMERGED; GitHub reports `mergeable=false`.
- Review submissions: zero. Inline review comments: zero. Conversation comments: one owner-authored continuation note about rejecting boolean FFprobe duration metadata; it does not constitute an independent review.
- PR #386 currently changes 25 files, including the single-clip renderer, media preflight, clipping implementation, regression tests, operator docs, startup prompt, registry, and this audit report.
- Base-to-head comparison reports DIVERGED: 187 commits ahead, 5 behind, with merge base `fd0d8925958760ce4b0f0617d64e98cb2b345690`. Do not rebase, retarget, or merge to reconcile this automatically.

## Source and regression-test review

Inspected the current branch versions of:
- `backend/app/single_clip_render.py`
- `backend/app/media_single_preflight.py`
- `backend/app/clipping.py`
- `tests/test_single_clip_render.py`
- `tests/test_media_single_preflight.py`
- `tests/test_clipping.py`
- `README.md` and `docs/SINGLE_CLIP_RENDER.md`

Observed guardrails:
- Dry-run is the default. Actual render requires both `--execute` and `--confirm-rights`; the rights flag is a local operator guardrail, not authenticated rights verification.
- Exactly one explicitly selected source and one clip are processed. The path does not enumerate directories or run a batch.
- Dry-run probes the selected original without copying it. Confirmed execution creates a bounded 1 MiB-chunk snapshot from a verified regular-file descriptor; FFprobe and FFmpeg consume the same snapshot bytes.
- Source and output paths reject symlinks/non-regular inputs where checked, and selected-file identity is rechecked around preflight/snapshot operations.
- Clip bounds are normalized and checked before snapshot I/O; duration is limited to 180 seconds and must fit within source duration.
- FFmpeg staging uses a private temporary directory on the destination filesystem. Final publication uses an atomic no-overwrite hard link.
- Post-render FFprobe verifies the output and duration. Failed verification attempts identity-checked cleanup; a replacement or uncertain output is intended to be preserved.
- JSON reports are exclusively reserved, newline-terminated, and report upload/publishing as disabled. No upload or publishing code is invoked by this renderer.
- Regression tests cover dry-run behavior, rights-gate ordering, invalid bounds and metadata, source mutation, symlink/path checks, no-overwrite behavior, private staging cleanup, output verification, and preservation of replaced output.

## Static-review caveat

The unverified-output cleanup helper performs a pathname `lstat()`, compares device/inode/type, and then calls pathname `unlink()`. Those two pathname operations are not atomic as a pair. A process able to modify the destination directory could theoretically replace the directory entry between the identity check and unlink. Therefore the current implementation is best-effort against ordinary replacement detected before unlink, but should not be described as providing an atomic adversarial-race guarantee. This audit is documentation-only and makes no runtime change; any stronger cleanup design needs a separately scoped implementation and regression review.

No other confirmed runtime defect was established within this bounded static inspection. This is not an independent external security review.

## Validation status

- Repository tests in this connector session: NOT RUN.
- Exact-head Ubuntu CI: NOT VERIFIED (zero associated runs).
- Exact-head hosted-Windows CI: NOT VERIFIED (zero associated runs).
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real-media render, playback, and owner acceptance: NOT VERIFIED.
- Synthetic tests or source code presence are not evidence of real GTA 6 media acceptance.

## Safety and dependency boundaries

- PR #386 remains OPEN / DRAFT / UNMERGED.
- Preserve its existing ancestry. PR #379's multi-file inventory conflicts with the later one-selected-video requirement.
- No workflow retry/dispatch, OAuth, credential access, real media, upload, publishing, merge, rebase, retarget, deployment, or destructive action was performed.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.

## Next action

Wait for a naturally triggered usable workflow run on the latest PR head, then inspect both Ubuntu and hosted-Windows jobs and logs against the exact checkout SHA. Obtain independent review. Do not infer success from a pending status with zero entries, and do not retry or dispatch workflows without owner direction.
