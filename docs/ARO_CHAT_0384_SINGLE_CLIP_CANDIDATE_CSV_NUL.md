# ARO-CHAT-0384 | Reject NUL in Single-Clip Candidate CSV (2026-11-26)

- Workstream: ARO-GTA-P0-384.
- Parent: existing single-clip renderer PR #386, exact head `9291fab827d20efa0fff8005aa62e9fda9dcec3d`.
- Branch: `workstream/aro-chat-0384-reject-nul-single-clip-candidate-csv-2026-11-26`.
- Scope: reject U+0000 while streaming the complete candidate CSV before `csv.DictReader` consumes each physical line.

## Change
- Added a streaming line wrapper that raises the existing controlled CSV validation path when a NUL character is present.
- Added regressions for NUL in an optional field, a header, an unselected trailing row, and a multiline quoted field.
- The full file remains validated, so an invalid trailing row cannot hide after the selected candidate.
- No media processing, source selection, OAuth, upload, or publishing behavior changed.

## Validation
- GitHub source read-back is required after commit.
- Repository unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg E2E: NOT RUN.
- Exact-head Ubuntu/Windows CI: NOT VERIFIED; recent approved retries still fail before any recorded steps, with zero billable runner time.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety
Keep the child PR OPEN / DRAFT / UNMERGED. No merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Stage 1 remains INCOMPLETE until its actual validation and owner-side acceptance gates pass.


## Exact-head Actions observation — run #45824908265 (2026-11-26)
- The run is associated with this PR head, `41e6b39c06983f69a7bcbbba39a6828b2097c73a`, and completed with conclusion `failure`.
- Windows job #139926481123 and Ubuntu job #139926481698 both completed with conclusion `failure`; the jobs response contained no recorded steps (`steps: null`) and no log URL. Direct step lookups returned empty arrays and log retrieval returned BlobNotFound in the prior inspection.
- Classification: `CI_FAILURE / EXECUTION_NOT_ESTABLISHED`. This run does not show checkout, compilation, or repository tests executing. The underlying cause remains UNVERIFIED; do not classify it as an application-code test failure or assert a runner-service root cause.
- No workflow retry or dispatch was initiated. Repository tests remain NOT RUN; synthetic FFmpeg E2E remains NOT RUN.


## Follow-up exact-head Actions run — #45828457264 (2026-11-26)
- This run is tied to the updated PR #412 head `ad10126537a04753154e98078d4afe80d2b76a86` (the documentation-evidence commit), event `pull_request`, workflow `.github/workflows/ci.yml`.
- Run #45828457264 completed FAILURE. Ubuntu job #139938629974 and Windows job #139938630458 both completed FAILURE in approximately 2–3 seconds; both job records have `steps: null`, no logs URL, and no artifacts.
- Check-run metadata reports one annotation for each job, but the connected GitHub fetch endpoint rejected the annotations URL. Annotation content is therefore NOT AVAILABLE in this session.
- This confirms the same pre-step failure pattern on the updated head; it still does not establish the underlying cause. Classification remains `CI_FAILURE / EXECUTION_NOT_ESTABLISHED`, root cause UNVERIFIED. Do not infer that repository tests ran or that the NUL guard caused the failure.
- No retry/dispatch was initiated. Unit tests NOT RUN; synthetic FFmpeg E2E NOT RUN.


## Runner-assignment evidence follow-up — 2026-11-26
- Inspected raw GitHub Actions job records (not only the connector's summarized step output) for four pull_request runs across separate PR heads: #45830244238 (PR #412, head `334d14fb6e23f5a725f3753b73cecaffacdd5145`), #45828457264 (PR #412, head `ad10126537a04753154e98078d4afe80d2b76a86`), #45806122307 (PR #407), and #45813736851 (PR #407 retry attempt).
- Every Ubuntu and Windows job record reports `runner_id: 0`, empty `runner_name`, empty `runner_group_name`, and an empty `steps` array. For the latest PR #412 run, job IDs are #139944807026 (Ubuntu) and #139944806116 (Windows); both failed before any step was recorded.
- This is stronger evidence that these jobs were never assigned a GitHub runner. It rules out claiming that checkout, compilation, unit tests, or FFmpeg smoke ran. It does NOT identify why runner assignment failed; exact GitHub-side cause remains UNVERIFIED. Do not attribute this to the CSV change, repository code, billing, or a GitHub outage without additional evidence.
- The workflow file itself defines normal `ubuntu-latest` and `windows-latest` matrix jobs with checkout, Python setup, FFmpeg install, compile, unit-test and synthetic smoke steps. No workflow edit is justified from the available evidence.
- No retry/dispatch was initiated. No production code or tests were changed in this follow-up. Repository tests and synthetic FFmpeg E2E remain NOT RUN; independent review NOT RECORDED; owner-device Windows NOT VERIFIED; authorized GTA 6 MP4 NOT PROCESSED. PR #412 and parent PR #386 remain OPEN / DRAFT / UNMERGED.
