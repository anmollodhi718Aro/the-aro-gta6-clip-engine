# ARO-CHAT-0367 | Preserve UTF-8 Creator Source IDs in Candidate CSV (2026-11-26)

## Scope
Extend the selected-candidate CSV encoding regression coverage to a valid UTF-8 source identifier containing non-ASCII characters. This is a test-only continuation on the existing draft PR #386 branch and base.

## Change
- Added a synthetic CSV fixture with a UTF-8 creator/source identifier (`creator-東京`).
- Asserted that `load_selected_candidate()` preserves the exact decoded source identifier and numeric clip metadata.
- Existing UTF-8 BOM + CRLF spreadsheet-export coverage remains unchanged.
- Production code unchanged. No media, FFmpeg/FFprobe, credentials, OAuth, upload, or publishing used.

## Validation
- Implementation commit: `a7be5bf80dd587cfee57d07d5c2f1e3644a7bf62` (test, report, registry, and startup handoff committed together).
- GitHub read-back: PRESENT for the regression test and report; registry and startup handoff entries also verified at the implementation commit.
- Local unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety and integration
Keep PR #386 OPEN / DRAFT / UNMERGED on its original branch/base. No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
