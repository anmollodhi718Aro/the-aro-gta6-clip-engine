# ARO-CHAT-0181 — Windows CI coverage for the local FFmpeg renderer

## Scope
Add hosted Windows CI coverage to the local, review-only FFmpeg renderer introduced by PR #263. Preserve Ubuntu coverage and ensure pull-request workflows run when this follow-up targets the feature branch.

## Change
- Convert CI to an Ubuntu/Windows matrix.
- Install FFmpeg/FFprobe using apt on Ubuntu and Chocolatey on Windows.
- Run the same Python 3.11 compile and unittest suite on both platforms.
- Remove the pull_request base-branch filter so this feature-branch follow-up receives CI.
- PR #264 was merged into the feature branch as squash commit `0c7d3226e903560a01e8335172f73088d5876ac1`.

## Exact-head validation
- PR #264 exact head: `c00f0b4070bc8941619b219897b609fa9368510c`.
- Python CI run #45371891963 (run 1166): SUCCESS.
- Ubuntu job #138367960376: compile passed; `Ran 16 tests in 0.698s; OK`; synthetic-video render/FFprobe test passed.
- Hosted-Windows job #138367959893: FFmpeg/FFprobe installation passed; compile passed; `Ran 16 tests in 0.434s; OK`; synthetic-video render/FFprobe test passed.
- Both jobs used merge ref `refs/remotes/pull/264/merge` at merge SHA `1186fdf`, combining PR #264 head with feature-branch base `e3b14d0b0ae175eacc19c6f5d6a999b5f343a7f1`. Raw-head-only checkout is NOT DEMONSTRATED.
- Same 16-test suite ran on each platform, not 32 unique tests.
- PR #264 is MERGED into the feature branch. The parent PR #263 advanced to `0c7d3226e903560a01e8335172f73088d5876ac1`; that new parent head has no associated run at the latest inspection. Do not transfer PR #264's CI result to PR #263's new head.

## Safety and remaining gates
- Synthetic media only. No GTA 6 footage, OAuth, credentials, upload, or publishing.
- Hosted Windows CI is not owner-device Windows verification.
- No video attachment was available in the current conversation; no user footage was processed.
- PR #263 remains OPEN / DRAFT / UNMERGED against main pending its own exact-head CI and review.
- Issue #68 remains OPEN. Keep live uploads/public publishing disabled pending independent human security review, owner-controlled integration, owner-device verification, device-appropriate upload-limit selection, and authorized real-media acceptance.
