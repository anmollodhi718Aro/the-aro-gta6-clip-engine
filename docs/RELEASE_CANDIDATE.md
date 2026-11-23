# Integrated Release Candidate — Review and Acceptance Plan

## What this branch consolidates

This branch integrates the existing MVP, timestamp candidate export, batch rendering, output/retry controls, review dashboard, candidate scoring, original content studio, source rights registry, rights-aware preflight, single-file THE ARO Studio, atomic clip-plan output and evidence-backed creator watchlist.

It is a consolidated review target, not a production release declaration.

## Required acceptance gates

### Gate 1 — Repository integrity
- [ ] Confirm this branch contains all intended modules.
- [ ] Review the final diff against main.
- [ ] Confirm no credentials, generated videos, local SQLite files or private user data are committed.

### Gate 2 — Test and CI
- [ ] `python -m compileall -q backend tests THE_ARO_STUDIO.py`
- [ ] `python -m unittest discover -s tests -v`
- [x] Confirm GitHub Actions reaches compile and test steps on the exact PR head in both Ubuntu and Windows.
- [x] Record test totals: run #942 at exact PR head `856e4d9c1afe299bac55176209a4bd87ce275240` passed all 249 tests on Ubuntu and all 249 tests on Windows; no tests were skipped.
- [x] Install FFmpeg/ffprobe in both CI environments and pass the synthetic MP4 render test on both.
- [x] Parse `scripts/check_project.ps1` and `scripts/manual_clip_wizard.ps1` on Windows CI, then run `scripts/check_project.ps1` successfully with FFmpeg/ffprobe available.

### Gate 3 — Local pipeline validation
- [ ] Start the local dashboard at 127.0.0.1.
- [ ] Generate an original content pack using supplied research notes.
- [ ] Register a synthetic permission record in a temporary database.
- [ ] Run rights preflight for permitted and blocked assets.
- [ ] Run candidate analysis against synthetic authorized chat data.
- [ ] Map the candidate plan using a measured single media-origin timestamp and separately using three synthetic clock anchors.
- [ ] Confirm clock-fit drift/residual rejection and calibrated-interval no-extrapolation.
- [ ] Dry-run batch rendering.
- [ ] Confirm actual execution probes media duration and blocks clips that exceed it.
- [x] Run the synthetic FFmpeg render in hosted Ubuntu and Windows CI; both passed.
- [ ] Owner-side: run `scripts/check_project.ps1` on the owner's Windows PC and save the compile/test summary.
- [ ] With an owner-supplied authorized local recording, run `START_CLIPPING_TODAY.bat`, verify multi-clip entry and dry-run output, then explicitly test the optional 9:16 render and local review dashboard.
- [ ] Confirm stopping at either confirmation prompt performs no render; only proceed with `RENDER` and `I CONFIRM RIGHTS` when the exact media and intended distribution are authorized.
- [ ] Verify dashboard report discovery and failed-only retry behavior.
- [ ] Generate the offline creator watchlist dashboard from synthetic ranking JSON.

### Gate 4 — External platform readiness
- [ ] Decide whether to implement Google OAuth + YouTube upload after a reviewed release candidate.
- [ ] Configure OAuth client credentials locally only; never commit them.
- [ ] Test with a private/unlisted owner-created video first.
- [ ] Keep final upload human-approved.

## Release boundary

Do not represent this software as a fully automated cloud clipping platform or a Play Store/Desktop production release until the external integrations, packaging, security and end-to-end tests above pass.
