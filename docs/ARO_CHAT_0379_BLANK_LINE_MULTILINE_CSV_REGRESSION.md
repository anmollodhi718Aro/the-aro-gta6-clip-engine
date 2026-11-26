# ARO-CHAT-0379 | Blank physical line inside quoted candidate CSV field

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-379
- Parent: PR #399, exact parent head `fea7ec2939de11841359bc7b748d9b7e609ee949`.
- Branch: `workstream/aro-chat-0379-accept-blank-lines-in-quoted-candidate-fields-2026-11-26`
- Scope: one synthetic parser regression only; production code, media processing, CI configuration, and uploader behavior are unchanged.

## Regression

- Add `tests/test_candidate_csv_blank_line_multiline.py`.
- Exercise a quoted optional `notes` field containing CRLF line endings and an empty physical line between two paragraphs.
- Verify the strict streaming parser accepts the valid CSV record and preserves the selected candidate's source identity and clip bounds.
- This complements the existing escaped-quote/multiline test, which covers non-empty continuation lines.

## Validation

- GitHub source write/read-back: pending.
- Local focused unit test: NOT RUN in this connector session.
- Full repository unit suite: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Independent review: NOT RECORDED.
- Authorized real GTA 6 MP4: NOT PROCESSED.
- Stage 1 and P0 pipeline: NOT COMPLETE.

## Safety

Keep this PR OPEN / DRAFT / UNMERGED. No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
