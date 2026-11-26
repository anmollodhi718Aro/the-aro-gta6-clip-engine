# ARO-CHAT-0322 — synthetic end-to-end render smoke test

- Chat ID: ARO-CHAT-0322
- Workstream ID: ARO-GTA-P0-322
- Exact title: ARO-CHAT-0322 | Synthetic End-to-End Single-Clip Smoke Test
- Parent: existing draft PR #386; existing branch and base preserved.

## Goal

Add a reproducible end-to-end check of the production one-selected-clip renderer using generated media only. This covers the real FFmpeg -> stable source snapshot -> FFprobe -> FFmpeg render -> output FFprobe -> output SHA-256 path, rather than mocking the renderer boundary.

## Implementation

Added `scripts/synthetic_single_clip_smoke.py`. It:
- creates an eight-second synthetic test pattern and tone in a temporary directory;
- renders only seconds 1 through 5 through `render_selected_clip()`;
- requires a `RENDERED` result, a non-empty output, and a 64-character output SHA-256;
- verifies upload and publishing remain disabled;
- deletes all generated media when the temporary directory closes; and
- prints a strict-JSON PASS/FAIL report.

The script accepts explicit FFmpeg and FFprobe executable names/paths. It does not enumerate user media, read third-party footage, retain artifacts, upload, or publish.

## Verification

- Implementation commit: `ecd9683e128500c13b7f0293c2f6848bfcd87193`.
- Local execution: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: PENDING; the branch workflow already has the two-OS matrix, but no run is claimed for this commit.
- Real authorized GTA 6 MP4: NOT PROCESSED / NOT VERIFIED.
- This synthetic smoke test is engineering verification only and does not satisfy real-media acceptance.

## Safety and handoff

- Keep PR #386 OPEN / DRAFT / UNMERGED and preserve its original base/ancestry.
- No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
