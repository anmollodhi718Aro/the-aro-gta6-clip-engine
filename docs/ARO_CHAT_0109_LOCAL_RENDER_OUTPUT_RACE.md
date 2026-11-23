# ARO-CHAT-0109: Local renderer output-race hardening

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0109
- Exact title: ARO-CHAT-0109 | Local Renderer Output-Race Hardening
- Workstream ID: ARO-GTA-P1-109
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0109-local-render-output-race-2026-11-24`
- Base: PR #169 head `5156eeb07b32a20bba2f60593f9e0b53fca07295`
- Parent: PR #169, Add permission-gated local FFmpeg clip renderer

## Finding
The original renderer wrote directly to the final output path and, on any caught failure, unconditionally unlinked that path. A concurrent process could create the destination after the initial existence check; if FFmpeg refused to overwrite it, cleanup could then delete the other process's file.

## Change
- Render to a private temporary directory under the destination parent.
- Probe and validate the staged MP4 before making it visible at the final local path.
- Use atomic `os.link(staged_output, destination)` for no-overwrite finalization. If another process creates the destination first, link creation fails and that file is preserved.
- Remove unconditional destination unlink cleanup. Temporary-directory cleanup is restricted to this invocation's staging area.
- Add a regression test that simulates a concurrent creator and asserts its file contents remain unchanged.

## Verification
- Parent PR #169 Ubuntu CI run #45249505815 passed its test job. This is predecessor evidence only.
- Local tests were not run in this connector session.
- Follow-up exact-head CI is pending. No test result is claimed yet.

## Safety
- No remote media, OAuth, credentials, network upload, public publishing, merge, retarget, or deployment.
- Only synthetic/mock-based tests are included. Owner-supplied media and documented rights are still required for any later real-media acceptance.