# ARO-CHAT-0306 — JSON-safe filesystem path reporting

- Static review found that the CLI serialized reports with `ensure_ascii=False`. On POSIX, filesystem paths may contain surrogate-escaped characters for non-UTF-8 filename bytes; writing such values through the UTF-8 report handle can raise `UnicodeEncodeError` after the exclusive RUNNING report has been created.
- Both initial and terminal report serialization now use ASCII escaping. The JSON remains valid UTF-8 and round-trips the path string through a standard JSON parser.
- Added `test_cli_json_reports_escape_surrogate_filesystem_names`, using a surrogate-escaped source path and a mocked dry-run renderer. It asserts the report is parseable and preserves the path value.
- Updated `docs/SINGLE_CLIP_RENDER.md`, the workstream registry, and startup handoff.
- Validation in this connector session: source/test edits committed; repository tests NOT RUN locally. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED.
- No real media was processed. No OAuth, credentials, upload, publishing, workflow retry/dispatch, merge, rebase, retarget, or deployment occurred. PR #386 remains OPEN / DRAFT / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
