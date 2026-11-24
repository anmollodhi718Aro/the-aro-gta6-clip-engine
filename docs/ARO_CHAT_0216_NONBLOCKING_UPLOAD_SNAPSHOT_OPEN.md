# ARO-CHAT-0216 | Prevent blocking on raced special-file upload sources

Date: 2026-11-24

## Finding
The ARO-CHAT-0215 upload snapshot helper checks that the source pathname is a regular file, then opens it with O_RDONLY and O_NOFOLLOW where available. A local path replacement between lstat() and open() could substitute a FIFO. Without O_NONBLOCK, opening that FIFO read-only can block before fstat() gets a chance to reject the non-regular descriptor.

## Change
- Add O_NONBLOCK to the source descriptor open flags where the platform exposes it.
- Add a regression test that replaces the checked source path with a FIFO immediately before the underlying open.
- The test asserts O_NONBLOCK is present before allowing the real open, then verifies the non-regular descriptor is rejected.
- The FIFO test skips only on platforms without os.mkfifo.

## Workstream
- Chat ID: ARO-CHAT-0216
- Exact title: ARO-CHAT-0216 | Prevent Blocking on Raced Special-File Upload Sources
- Workstream ID: ARO-GTA-P1-216
- Branch: `workstream/aro-chat-0216-nonblocking-upload-snapshot-open-2026-11-24`
- Base / starting SHA: PR #328 head `114e5bfc4b154e0da272ed36408ab156cfdc5ab9`
- Parent: Draft PR #328, approved-byte snapshot implementation
- Code commit: `9d397a0aacb1687d64acd780d321c54fbf6647ff`
- Test commit: `ec46588884806c5b173340bfadcaccd47057997a`

## Validation
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu and hosted-Windows CI: PENDING; branch is not yet in a PR.
- No OAuth, credentials/tokens, real media, network upload, merge, deployment, or publishing performed.
- No live upload behavior was invoked.

## Safety
Draft-only follow-up stacked on PR #328. Keep Issue #68 OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled. Do not merge, rebase, retarget, deploy, or perform a real upload.
