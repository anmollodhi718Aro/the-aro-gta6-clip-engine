# ARO-CHAT-0253 — Scale rendered clip duration tolerance

Date: 2026-11-25

## Scope
Continue the existing PR #386 / ARO-GTA-P1-244 single-selected-clip renderer. No new branch or PR.

## Finding
The post-render FFprobe check previously accepted a fixed ±1.0-second duration difference. For a very short requested clip, that could classify an almost-empty output as RENDERED even though it did not represent the requested interval.

## Change
- Require the reported rendered duration to be finite and strictly positive.
- Replace the fixed tolerance with a duration-scaled tolerance: 2% of the requested duration, bounded below by 0.05 seconds and above by 1.0 second.
- Add a regression for a 0.1-second requested clip whose synthetic output reports only 0.01 seconds; the report must be FAIL.

## Commits
- Production: 844d080a0b40e822253287adf943bedef456769a
- Regression test: 853b93e43a2228d26b66cc914eeca7922db1a9ab

## Validation
- Focused and repository tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- No real media was processed.

## Safety and integration
- PR #386 remains DRAFT / OPEN / UNMERGED.
- Preserve the existing #383 -> #380/#379 ancestry; PR #379 conflicts with the one-selected-video requirement. Do not merge, rebase, retarget, or integrate without owner approval.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Live uploads and public publishing remain disabled.
- No OAuth, credentials, upload, publishing, workflow retry/dispatch, or deployment occurred.
