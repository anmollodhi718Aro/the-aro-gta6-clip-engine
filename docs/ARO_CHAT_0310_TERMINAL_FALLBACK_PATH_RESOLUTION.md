# ARO-CHAT-0310 — contain terminal fallback path-resolution errors

- Workstream: ARO-GTA-P1-310.
- Continued the existing draft PR #386 and its current branch; no new branch or PR.
- Production commit: `d17f71d1b19ea0848e655bde41a08846585317c2`.
- The exclusive terminal-report fallback now resolves the fallback path and protected source/output paths inside a guarded validation block. `OSError`, `RuntimeError` (including symlink-loop resolution), and `ValueError` are normalized to an `OSError` with a clear safety message.
- This keeps path-validation failures inside the existing fallback-creation error handler. If terminal report persistence fails after rendering, the CLI emits the manual-output-inspection warning and returns the report-write failure code rather than allowing a path-resolution exception to escape and obscure the fact that an output may already exist.
- Regression coverage is present in `tests/test_single_clip_render.py`: it simulates a completed render, a partial terminal-report write, and a symlink-loop error while resolving the fallback path; it asserts exit code 2, preservation of the completed output, no unsafe fallback file, and an operator warning.
- Latest exact-head Actions run: #45744189317, job #139656150344, on `d17f71d1b19ea0848e655bde41a08846585317c2`. GitHub reports the check as failed, but the job has an empty step list and no runner metadata; log retrieval returned BlobNotFound. This is a pre-step runner/infrastructure failure, not evidence that Python tests failed. Root cause remains UNKNOWN. Do not claim tests passed or failed.
- Local repository tests NOT RUN in this connector session. Independent review NOT RECORDED. Owner-device Windows verification NOT VERIFIED. Real authorized MP4 NOT PROCESSED.
- PR #386 remains OPEN / DRAFT / UNMERGED, with its original base and ancestry. Do not merge, rebase, retarget, dispatch/retry workflows, or deploy without explicit owner approval.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. OAuth, credentials, real media, upload, and public publishing remain unused/disabled.
