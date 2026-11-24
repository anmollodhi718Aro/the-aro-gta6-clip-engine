# ARO-CHAT-0181 — Windows CI coverage for the local FFmpeg renderer

## Scope
Add hosted Windows CI coverage to the local, review-only FFmpeg renderer introduced by PR #263. Preserve Ubuntu coverage and ensure pull-request workflows run when this follow-up targets the feature branch.

## Baseline evidence
- Parent PR: https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/263
- Parent head: `9ad8bb29381a703057729fd0f2ef50ede2dbf743`
- Parent run: https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45355982338
- Ubuntu job #138313784237 passed compileall, all 16 discovered tests, and synthetic MP4/FFprobe integration.
- Parent workflow had one Ubuntu job only. No hosted-Windows result existed.

## Change
- Convert CI to an Ubuntu/Windows matrix.
- Install FFmpeg/FFprobe using apt on Ubuntu and Chocolatey on Windows.
- Run the same Python 3.11 compile and unittest suite on both platforms.
- Remove the pull_request base-branch filter so this feature-branch follow-up receives CI.

## Validation
Pending exact-head CI for this workstream. Do not transfer parent PR #263's Linux result to this branch. No local tests run in this connector session.

## Safety and remaining gates
Synthetic media only. No GTA 6 footage, OAuth, credentials, upload, publishing, merge, retarget, deployment, or destructive actions. Hosted Windows CI is not owner-device Windows verification. Real-media render and owner playback acceptance remain outstanding.
