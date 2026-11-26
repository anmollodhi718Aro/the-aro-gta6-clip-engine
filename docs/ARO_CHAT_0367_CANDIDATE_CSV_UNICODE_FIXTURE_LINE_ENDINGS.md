# ARO-CHAT-0367 | Correct Unicode Candidate CSV Fixture Line Endings

- Workstream: ARO-GTA-P0-367; continued the existing draft PR #386 on its original branch and base. No new branch or PR.
- Static source review found that `test_preserves_non_ascii_creator_source_id` wrote the two CSV records with literal backslash-`n` characters instead of record separators. The fixture therefore formed one malformed header record and could not prove Unicode source-ID compatibility.
- Corrected the fixture string literals to use actual newline characters while retaining UTF-8 encoding and the non-ASCII source ID `creator-東京`.
- Changed file: `tests/test_candidate_csv_encoding.py`.
- Test commit: `7bfd5c52baa88796e911de1f4a95798e6b130a18`.
- Validation: GitHub source write completed. Local test NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- No production behavior changed. No media, OAuth, credentials, upload, publishing, workflow retry/dispatch, merge, rebase, retarget, or deployment.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and its original ancestry. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
