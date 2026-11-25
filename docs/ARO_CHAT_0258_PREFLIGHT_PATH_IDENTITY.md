# ARO-CHAT-0258 | Harden Single-Video Preflight Path Identity

- Exact chat title: `ARO-CHAT-0258 | Harden Single-Video Preflight Path Identity`
- Workstream: `ARO-GTA-P1-258`
- Follow-up to PR #386 / ARO-GTA-P1-244 on the existing branch `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`; no new branch or PR and no ancestry changes.
- Finding: the standalone read-only FFprobe preflight checked the selected path with `is_symlink()` and `stat()`, then compared only size, mtime, and inode after probing. A path could be replaced by a symlink during the probe, and on POSIX an in-place same-size mutation with restored mtime could evade the existing comparison.
- Change: preflight now uses `lstat()` before and after FFprobe, requires a regular non-symlink file, compares path and followed-file device/inode/type identity, and checks ctime on POSIX to detect in-place mutation even if mtime is restored. Windows ctime is excluded because it represents creation time there.
- Regression coverage: selected-path replacement with a symlink during mocked FFprobe; POSIX in-place mutation with size and mtime restored. Windows skips only the POSIX ctime-specific case.
- Changed files: `backend/app/media_single_preflight.py`, `tests/test_media_single_preflight.py`, `docs/SINGLE_CLIP_RENDER.md`, and this report, with startup/registry handoff synchronization.
- Production commit: `bef1fc7de56d5ae48d0390b727b43f18ac008716`; regression commit: `c7ffdafda71f45fe1af6c725235d33c5bc537c43`; operator documentation commit: `dcbc4e4ac5ae552aa22f45e53b3044d0081ec95c`.
- Repository tests NOT RUN in this connector session. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows and real authorized media NOT VERIFIED.
- PR #386 remains DRAFT / OPEN / UNMERGED. Preserve its existing #383 -> #380/#379 ancestry; no merge, rebase, retarget, or integration without owner approval.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled. No real media, OAuth, credentials, upload, publishing, workflow retry/dispatch, or deployment.
