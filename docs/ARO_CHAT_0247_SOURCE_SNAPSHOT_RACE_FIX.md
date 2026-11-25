# ARO-CHAT-0247 — Source snapshot race elimination

Date: 2026-11-25  
Repository: anmollodhi718Aro/the-aro-gta6-clip-engine  
Existing workstream: ARO-GTA-P1-244 / PR #386  
Branch: workstream/aro-chat-0244-single-selected-clip-render-2026-11-25

## Finding

The previous renderer checked the selected path immediately before invoking FFmpeg, but the path could still be replaced between that check and FFmpeg opening it. The bytes rendered were therefore not provably the same bytes that passed FFprobe.

## Change

- Open the one selected source as a file descriptor, rejecting symlinks and non-regular files.
- Compare descriptor identity and metadata against the selected pathname before copying.
- Copy in bounded 1 MiB chunks into a private temporary snapshot, checking descriptor metadata, pathname identity, and copied byte count after the copy.
- Run both FFprobe preflight and FFmpeg rendering against the same snapshot path.
- Remove the temporary snapshot when the invocation exits.
- Add a regression that proves preflight and renderer receive the same snapshot path.

This avoids whole-video RAM buffering. Temporary disk use is proportional to the selected source size. It does not scan directories or process more than one explicitly selected source.

## Commits

- Production: 29652582a611bec667497b79fac9729e3f0718c5
- Tests: fb4d4987e61d6d2af2130318494d394aed0caef6
- Operator docs: 5cbb5cfa28b5857aadd5907f2b21f25b0282d91e
- Registry: d222c6575f3c4736680564a0308dad87240b0483
- Startup handoff: dbbea493dbb4a830fb5b8f31e19378abacbeb9fb

## Validation

- Repository unit tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: NOT YET CHECKED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Real authorized media: NOT PROCESSED / NOT VERIFIED.

## Safety and integration

PR #386 remains DRAFT / OPEN / UNMERGED. Preserve its existing ancestry through PR #383 and PRs #380/#379. PR #379's multi-file inventory conflicts with the later one-selected-video requirement; do not merge, rebase, retarget, or integrate without explicit owner approval.

Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled. No OAuth, credentials, real media, upload, publishing, workflow retry/dispatch, merge, or deployment occurred.
