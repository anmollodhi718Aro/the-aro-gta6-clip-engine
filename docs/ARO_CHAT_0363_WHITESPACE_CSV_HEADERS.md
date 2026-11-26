# ARO-CHAT-0363 | Reject Whitespace-Only Candidate CSV Headers

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-363
- Scope: focused regression coverage on the existing draft PR #386 branch; no production behavior change.
- Finding: the candidate CSV loader rejects blank header cells, including `None` and empty strings. Its `strip()` check should also reject headers containing only whitespace; this boundary was not directly covered by the preceding ARO-CHAT-0361/0362 regressions.
- Change: added two synthetic CSV regressions for a whitespace-only middle header cell and a whitespace-only trailing header cell. Both require `load_selected_candidate()` to fail closed with the existing blank/duplicate-column validation error.
- Test file: `tests/test_candidate_csv_blank_headers.py`.
- Commits: initial test commit `b70e8f5e7b0642e1cc88cdf50c9fd00472f7035a`; fixture-source correction `1eb3fdc6ed0eebbf2d7c429c0cbbebeefd94c06d`.
- Production code unchanged. Synthetic CSV fixtures only; no media tools, media processing, OAuth, credentials, upload, or publishing.
- Validation: GitHub source read-back only. Unit tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED on its original ancestry. No workflow dispatch/retry, merge, rebase, retarget, deployment, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
