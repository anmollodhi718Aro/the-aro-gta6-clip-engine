# ARO-CHAT-0198 / PR #301 Exact-Head CI Audit

Date: 2026-11-24

## Scope
Documentation-only closeout for PR #301 / ARO-GTA-P1-198. The implementation under test adds the second destination profile's canonical token-path assertion in `tests/test_youtube_upload.py`. No production code was changed by this workstream.

## Pull request and refs
- PR: https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/301
- State at audit: OPEN / DRAFT / UNMERGED
- Head branch: `workstream/aro-chat-0198-canonical-profile-path-regression-2026-11-24`
- Audited PR head: `4dce542aa59023a7dc0ca9c61badecf4f0734f59`
- Base branch: `workstream/aro-chat-0134-private-upload-response-verification-2026-11-24`
- Base SHA: `97250fbb3bf1fd8d9e5e03dfc6ac6a9267b643b5`
- Both CI jobs checked out PR merge ref SHA `d961d60d45337ba58dbcc566b661545c673a5ce7`, merging the audited head into the stated base. Raw-head-only checkout is NOT DEMONSTRATED.

## Actions evidence
- Workflow: Python CI
- Run: [#45399961380](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45399961380)
- Run conclusion: SUCCESS
- Ubuntu job: #138465638360, SUCCESS
- Hosted Windows job: #138465637811, SUCCESS
- Both jobs compiled source/tests, ran the complete unittest suite, and rendered/verified a synthetic MP4 with FFprobe.
- Ubuntu: 346 tests passed in 3.652s.
- Hosted Windows: 346 tests passed in 12.782s.
- The same 346-test suite passed on both platforms.

## Synthetic-only safety evidence
Both job logs report:
- `upload_performed=false`
- `gta6_footage_used=false`
- `third_party_media_used=false`
- `publishing_enabled=false`
- `manual_review_required=true`

No live OAuth, credentials/tokens, real media, YouTube API upload, or public publishing was used.

## Review and remaining gates
- PR #301 review submissions: none observed.
- PR #301 inline review threads: none observed.
- PR #301 conversation comments: none observed.
- Independent security review: NOT RECORDED.
- Issue #68 remains OPEN.
- Owner-device verification, source-rights evidence, exact per-clip approval, owner-controlled integration, device-appropriate upload memory limit selection, and separately authorized real-media acceptance remain outstanding.
- Live uploads and public publishing remain disabled.

## Conclusion
PR #301's current head is validated by successful Ubuntu and hosted-Windows merge-ref CI: compilation, 346 tests per platform, and synthetic MP4/FFprobe. This does not constitute independent security approval, owner-device acceptance, raw-head-only CI proof, merge authorization, or permission for live uploads/public publishing.
