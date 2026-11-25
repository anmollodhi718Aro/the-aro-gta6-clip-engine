# ARO-CHAT-0238 | Exhaustive IDNA Numeric-Mapping Regression

Date: 2026-11-25

## Scope
Test-only continuation on existing draft PR #376 / ARO-GTA-P1-238. No new branch or PR.

## Finding
The existing URL-host guard operates after Python's built-in IDNA codec. Earlier regressions covered representative compatibility digits, but did not systematically enumerate all Unicode numeric-category characters that the active codec maps to ASCII-only decimal labels.

## Change
- Added `unicodedata`-driven coverage in `tests/test_rights_registry.py`.
- The test enumerates Unicode numeric-category code points, retains characters whose IDNA encoding becomes an ASCII decimal label, and asserts each corresponding `example.<character>` URL is rejected by the source-rights registry.
- This covers the active Python runtime's complete set of such mappings without hard-coding a Unicode-version-specific list.
- No production code, uploader, OAuth, media, workflow configuration, or publishing behavior changed.

## Validation
- Isolated in-memory probe against the current hostname-validation logic enumerated 131 mapped characters; all 131 were rejected.
- Canonical IPv4 controls `192.0.2.1` and `192.0.2.1.` remained accepted in the same probe.
- This probe is not a repository unit-test run.
- Repository unit tests: NOT RUN in this connector session.
- Exact-head Python CI for commit `bbffafc8fe976915bcc3cabbcb050016751e2797`: run #45538802378 completed FAILURE. Ubuntu job `138951930368` and hosted-Windows job `138951930049` both exposed `steps: null` and `logs_url: null`. Failure phase/root cause NOT VERIFIED; no compile or test result is claimed and failure is not attributed to application code.
- PR #376 review submissions and inline review threads were empty at inspection. Independent review NOT RECORDED.

## Safety and disposition
- Preserve PR #376 OPEN / DRAFT / UNMERGED.
- Issue #68 remains OPEN / NOT IMPLEMENTED / WAITING_FOR_OWNER_APPROVAL; owner UNASSIGNED.
- Keep live uploads and public publishing disabled.
- No workflow retry/dispatch, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing was performed.
