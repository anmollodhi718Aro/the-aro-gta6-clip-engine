# ARO-CHAT-0329 | Wire Synthetic Clip Smoke Into CI

- Chat ID: ARO-CHAT-0329
- Exact chat title: ARO-CHAT-0329 | Wire Synthetic Clip Smoke Into CI
- Workstream ID: ARO-GTA-P0-329
- Scope: correct the synthetic smoke digest-mismatch fixture and ensure the generated-media end-to-end smoke executes on both hosted operating systems in the existing CI matrix.
- Existing branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Existing PR: #386, OPEN / DRAFT / UNMERGED; original base and ancestry preserved.

## Changes

- Install FFmpeg on Ubuntu using apt and on Windows using Chocolatey.
- Compile the `scripts` package in CI.
- Run the complete unit suite and then `python -m scripts.synthetic_single_clip_smoke` on both Ubuntu and Windows jobs.
- Corrected the digest-mismatch fixture to return a valid-format but incorrect all-zero SHA-256 and removed a duplicate import. Later smoke-test continuation commits retain the corrected mismatch behavior.
- No new branch or PR was created.

## Commits

- CI workflow: `2437e2e9590065c92e574dd917f33b80faf343a0`
- Test fixture correction: `b403cfd3b641ef3f717536151ef1012fa1046009`
- Report: `docs/ARO_CHAT_0329_SYNTHETIC_SMOKE_CI.md`

## Validation

- Active-branch workflow source re-read: IMPLEMENTED.
- Workflow lookup for the workflow commit returned zero associated runs.
- Latest recorded startup-handoff commit at audit time had zero associated workflow runs and zero combined status entries.
- Local unit tests: NOT RUN.
- Actual synthetic FFmpeg smoke: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: PENDING / NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED / NOT VERIFIED.

## Safety

Synthetic pattern and tone only. No user or third-party footage, OAuth, credentials, live upload, public publishing, merge, rebase, retarget, deployment, workflow retry, or manual dispatch. Upload and publishing remain disabled. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
