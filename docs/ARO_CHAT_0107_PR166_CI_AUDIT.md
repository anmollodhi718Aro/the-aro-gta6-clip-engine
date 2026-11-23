# ARO-CHAT-0107 PR #166 exact-head CI audit

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0107
- Exact title: ARO-CHAT-0107 | PR #166 Exact-Head CI Audit
- Workstream ID: ARO-GTA-P1-107
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Role: Documentation-only exact-head CI evidence auditor

## Task
Audit PR #166's own commit-associated GitHub Actions run, Ubuntu and hosted-Windows jobs, compile/tests, synthetic MP4/FFprobe validation, checkout refs, and review state. Record observed evidence only.

## Branch and ancestry
- Branch: `workstream/aro-chat-0107-pr166-exact-head-ci-audit-2026-11-24`
- Base / starting SHA: PR #166 head `4e2e74805c2e4c21aa246a4765e66c0a97cc7be2`
- Parent PR under audit: #166
- Duplicate check: ARO-CHAT-0106 branch exists for a separate Issue #68 rights-registry task and was left untouched. No ARO-CHAT-0107 branch or PR existed at reservation.
- Planned changes: this report, `docs/CHAT_WORKSTREAM_REGISTRY.md`, `docs/ARO_CHAT_STARTUP_PROMPT.md`, and `docs/ARO_PERMISSION_AND_APPROVAL_LEDGER.md`.
- Scope: documentation-only; no application, uploader, test, renderer, media-ingestion, or workflow behavior changes.

## Initial exact-head snapshot
- Audited PR #166 head: `4e2e74805c2e4c21aa246a4765e66c0a97cc7be2`.
- Commit-associated Python CI run [#45243626968](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45243626968), run 977, is IN_PROGRESS.
- Ubuntu job #137934533544: setup, checkout, and Python setup succeeded; FFmpeg/FFprobe installation was in progress; compile, unit tests, and synthetic render were pending.
- Hosted-Windows job #137934534056: job setup succeeded; checkout was in progress; Python setup, FFmpeg/FFprobe, compile, unit tests, and synthetic render were pending.
- Combined commit status returned no status entries at inspection. PR #166 review submissions and inline review threads were empty.
- No final compile/test/render conclusion, test count, checkout SHA, or merge-ref/raw-head distinction is claimed. Re-fetch both jobs and decoded logs after completion.
- No local tests were run in this connector session.

## Safety and owner gates
- Issue #68 remains OPEN / UNASSIGNED / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled pending owner assignment and canonical authenticated-uploader PR selection or approved consolidation.
- Hosted Windows CI is not owner-device verification; synthetic media is not real GTA 6 media acceptance.
- No credentials/tokens, OAuth session, real media, network upload, public publishing, merge, retarget, deployment, rebase, force-push, or destructive action was performed.

## Closeout checklist
- [ ] Re-fetch run #45243626968 and confirm final conclusion.
- [ ] Inspect Ubuntu and hosted-Windows job logs separately.
- [ ] Record compile result and exact test counts/durations.
- [ ] Verify synthetic render report and FFprobe output on each job.
- [ ] Record actual checkout refs and distinguish merge-ref from raw-head checkout.
- [ ] Re-check independent PR reviews and combined status.
- [ ] Update this report and registry with evidence; do not claim owner-device or real-media verification.


## Ubuntu job closeout update
- Ubuntu job #137934533544 completed SUCCESS. The decoded log confirms Python 3.11.18, source compilation success, and `Ran 334 tests in 4.414s` with the unit-test step successful.
- The job checked out `refs/remotes/pull/166/merge` at merge SHA `c0830db5375becbc50b8fac9a5eb158a8d13a475`, merging audited PR #166 head `4e2e74805c2e4c21aa246a4765e66c0a97cc7be2` into base `546906fca62ff2493a7ae1955dfdd1b4948233f2`. Raw-head-only checkout is NOT DEMONSTRATED.
- The synthetic test report states source type is a locally generated synthetic test pattern and tone, `gta6_footage_used=false`, `third_party_media_used=false`, source duration 8.0 seconds, rendered duration 4.0 seconds, `publishing_enabled=false`, and `manual_review_required=true`. The workflow's synthetic render/verification step concluded SUCCESS.
- Hosted-Windows job #137934534056 remained IN_PROGRESS at this refresh while FFmpeg/FFprobe installation was running; no Windows compile/test/render result is claimed.
- PR #166 matrix CI remains IN_PROGRESS / NOT VERIFIED until the Windows job completes. Ubuntu's 334 tests are not evidence for Windows. No test count is doubled across platforms.


## Hosted-Windows job closeout update
- Hosted-Windows job #137934534056 completed successfully through checkout, Python 3.11 setup, FFmpeg/FFprobe installation, compilation, the full unit-test suite, and synthetic MP4 render/verification.
- Decoded log reports `Ran 334 tests in 15.827s`; the unit-test step succeeded.
- The job checked out `refs/remotes/pull/166/merge` at the same merge SHA `c0830db5375becbc50b8fac9a5eb158a8d13a475`, merging PR #166 head `4e2e74805c2e4c21aa246a4765e66c0a97cc7be2` into base `546906fca62ff2493a7ae1955dfdd1b4948233f2`. Raw-head-only checkout is NOT DEMONSTRATED.
- Windows synthetic report confirms locally generated synthetic pattern/tone only, `gta6_footage_used=false`, `third_party_media_used=false`, source duration 8.0 seconds, rendered duration 4.0 seconds, `publishing_enabled=false`, and `manual_review_required=true`.
- Both platforms ran the same 334-test suite; this is not 668 unique tests.
- Run #45243626968 has successful Ubuntu and hosted-Windows jobs. PR #166's required CI matrix is CI_VERIFIED on the PR merge ref, not raw-head-only CI. Hosted Windows is not owner-device verification, and synthetic media is not real GTA 6 footage.

## Follow-up branch verification
- Follow-up PR #167 head: `766d5cc9d2bce6b1ff20640a01d3da36ec2733c8`.
- Commit-associated workflow lookup and combined commit status returned zero entries at the latest check. PR #167's own exact-head CI is PENDING / NOT VERIFIED; do not transfer PR #166's successful run to this documentation follow-up.
