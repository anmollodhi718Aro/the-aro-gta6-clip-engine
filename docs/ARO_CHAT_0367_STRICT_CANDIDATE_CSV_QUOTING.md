# ARO-CHAT-0367 | Reject Trailing Text After Quoted Candidate CSV Fields

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-367
- PR: #386, retained OPEN / DRAFT / UNMERGED on its existing dependency chain.
- Branch: `workstream/aro-chat-0367-strict-candidate-csv-quoting-2026-11-26`
- Starting SHA: `f65c1a199b126c122332a5c7fd62b159411cbefb`
- Task: add a focused parser regression for characters appearing after a closed quoted CSV field.
- Changed file: `tests/test_candidate_csv_strict_quoting.py`
- Test commit: `e450ee36e26f172a71bb35bcd7351adffefcd4c1`

## Change

Added a synthetic CSV fixture with a valid selected first row followed by a malformed later row whose quoted final field is immediately followed by trailing text. The loader must parse the complete file with strict CSV quoting and reject the malformed later record rather than returning the earlier selected candidate.

Production code unchanged. The test uses temporary CSV text only; no FFmpeg/FFprobe process, real footage, credentials, OAuth, network upload, or publishing is involved.

## Verification

- GitHub write: completed for the test file.
- Source read-back: pending.
- Local unit test: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety and handoff

Preserve PR #386 OPEN / DRAFT / UNMERGED and its original base/ancestry. Do not dispatch or retry workflows, merge, rebase, retarget, deploy, use OAuth/credentials, process real media, upload, or publish without the required explicit owner authorization. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
