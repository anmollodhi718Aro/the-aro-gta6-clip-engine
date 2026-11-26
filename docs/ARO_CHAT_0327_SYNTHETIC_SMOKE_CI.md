# ARO-CHAT-0327 | Wire Synthetic Clip Smoke Into CI

- Chat ID: ARO-CHAT-0327
- Exact chat title: ARO-CHAT-0327 | Wire Synthetic Clip Smoke Into CI
- Workstream ID: ARO-GTA-P0-327
- Scope: ensure the synthetic single-selected-clip end-to-end smoke executes automatically on both hosted operating systems in the existing CI matrix.
- Existing branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Existing PR: #386, OPEN / DRAFT / UNMERGED; original base and ancestry preserved.

## Changes

- Added explicit FFmpeg installation on Ubuntu via apt and Windows via Chocolatey.
- Added the `scripts` package to the Python compile step.
- Added `python -m scripts.synthetic_single_clip_smoke` after the full unit-test suite on both Ubuntu and Windows jobs.
- No new branch or PR was created. Existing digest-verification and smoke failure-path tests remain attributed to their own workstreams.

## Commits

- CI workflow: `2437e2e9590065c92e574dd917f33b80faf343a0`
- Report: `docs/ARO_CHAT_0327_SYNTHETIC_SMOKE_CI.md`
- Registry and startup handoff: pending.

## Validation

- Workflow source re-read from the active branch: IMPLEMENTED.
- Exact-head workflow lookup for the workflow commit: zero associated runs returned.
- Current startup-handoff commit `66d9e76c8d679ea183568b32f78b352c35fe55cd`: zero associated workflow runs and zero combined status entries at audit time.
- Local unit tests: NOT RUN.
- Actual synthetic FFmpeg smoke: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: PENDING / NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED / NOT VERIFIED.

## Safety

Synthetic pattern and tone only. No user/third-party footage, OAuth, credentials, live upload, public publishing, merge, rebase, retarget, deployment, workflow retry, or manual dispatch. Upload and publishing remain disabled. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
