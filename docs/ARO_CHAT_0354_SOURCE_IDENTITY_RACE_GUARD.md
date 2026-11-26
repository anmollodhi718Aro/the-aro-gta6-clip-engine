# ARO-CHAT-0354 | Reject Source-Inode Alias Introduced Before Output Open

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-354
- Parent: existing draft PR #386; original branch and base preserved.
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Scope: close the source/output path-swap window in the synthetic smoke verifier. No real media or upload behavior.

## Finding

The harness previously called `os.path.samefile(source, output)` before hashing the output. A path could be replaced with a hard link to the source after that check but before `_hash_verified_output()` opened it. The verifier checked that the opened descriptor matched the output path, but did not compare the opened inode with the source inode.

## Change

- `_hash_verified_output` now accepts an optional `distinct_from` path.
- When supplied, it compares the opened regular output descriptor's device/inode with the source path's device/inode and rejects an alias.
- The synthetic smoke harness supplies its generated source path during final output verification.
- Added `tests/test_synthetic_smoke_source_identity_race.py`, which replaces the output with a source hard link immediately before the verifier's `os.open` and requires fail-closed rejection.
- The test uses generated temporary bytes only and skips if hard-link creation is unavailable.

## Commits

- Production: `891df35f87e940453ab2be6b0880c844f31dacf8`
- Regression: `3d781618011096e50078c669afb523dcc9dfbed3`

## Validation

- GitHub source write: completed; read-back and exact-head workflow lookup pending.
- Local unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety and handoff

Keep PR #386 OPEN / DRAFT / UNMERGED on its original ancestry. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
