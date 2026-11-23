# ARO-CHAT-0108: Local Renderer Output Race Hardening

## Attribution
- Chat ID: ARO-CHAT-0108
- Exact chat title: ARO-CHAT-0108 | Harden local renderer output race
- Workstream ID: ARO-GTA-P1-108
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: workstream/aro-chat-0108-render-output-race-hardening-2026-11-24
- Base branch: feature/local-ffmpeg-renderer
- Starting SHA: 5156eeb07b32a20bba2f60593f9e0b53fca07295
- Parent implementation: PR #169

## Finding
The original renderer wrote FFmpeg output directly to the final destination and unconditionally unlinked that destination on selected failures. If another process created the output after the initial existence check, FFmpeg's no-overwrite refusal could be followed by cleanup deleting the competing process's file.

## Changes
- Render into a private temporary directory created beside the destination.
- Probe and validate the staged MP4 before exposing it at the requested path.
- Publish the validated file with an atomic same-filesystem hard link (os.link), which fails if the destination already exists.
- Remove destination-unlink error cleanup; temporary-directory cleanup is isolated from the final path.
- Add regression coverage for a competing writer winning the destination race and for FFprobe failure leaving the final path absent.
- Document the staging and atomic create-if-absent behavior.

## Verification
- Parent PR #169 CI run #45249505815 passed on the GitHub Actions merge ref: Python compile passed and 12 tests passed. This is predecessor evidence only.
- This workstream's own CI: PENDING until its exact PR head and job logs are inspected.
- Local tests in this connector session: NOT RUN.
- Real authorized media, owner-device Windows, and publishing: NOT VERIFIED / OUT OF SCOPE.

## Safety boundary
- Synthetic/mock-based tests only.
- No platform scraping, stream downloading, OAuth, credential access, network upload, public publishing, merge, retarget, deployment, or destructive operation.
- Existing output files are never overwritten or removed by renderer error cleanup.