# ARO-CHAT-0325 | Correct Smoke Digest Regression

- Chat ID: ARO-CHAT-0325
- Exact chat title: ARO-CHAT-0325 | Correct Smoke Digest Regression
- Workstream ID: ARO-GTA-P0-325
- Scope: correct the synthetic smoke test that claimed to test digest mismatch but supplied a matching digest; retain the CI end-to-end smoke integration on both hosted operating systems.
- Existing branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Existing PR: #386, OPEN / DRAFT / UNMERGED. Original base and ancestry preserved.

## Findings and changes

- The previous mismatch regression wrote `synthetic-rendered-mp4` but returned the SHA-256 of those same bytes, while asserting that a mismatch exception should occur. The test setup contradicted its expected result.
- The regression now returns a valid-format but incorrect all-zero SHA-256, so the production comparison must reject it.
- Removed a duplicate `hashlib` import introduced during concurrent edits.
- The CI workflow now installs FFmpeg on Ubuntu and Windows, compiles the `scripts` package, runs the complete unit suite, and invokes `python -m scripts.synthetic_single_clip_smoke` on both matrix jobs.

## Commits

- CI integration: `2437e2e9590065c92e574dd917f33b80faf343a0`
- Test fixture correction: `b403cfd3b641ef3f717536151ef1012fa1046009`
- Earlier concurrent ARO-CHAT-0324 output-digest implementation remains separately attributed in the registry; no history was rewritten.

## Validation status

- Static source inspection: IMPLEMENTED.
- Local unit tests: NOT RUN in this connector session.
- Actual synthetic FFmpeg smoke: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: PENDING / NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED / NOT VERIFIED.

## Safety

Synthetic test pattern and tone only. No user or third-party footage, OAuth, credentials, live upload, publishing, deployment, merge, rebase, retarget, workflow retry, or manual workflow dispatch. Upload/publishing remain disabled. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
