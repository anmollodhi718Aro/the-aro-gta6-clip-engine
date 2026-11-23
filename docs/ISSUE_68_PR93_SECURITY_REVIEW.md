# Issue #68: PR #93 bounded security review

**Review workstream:** ARO-CHAT-0057 / ARO-GTA-P1-57  
**Review date:** 2026-11-23  
**Reviewed repository:** anmollodhi718Aro/the-aro-gta6-clip-engine  
**Reviewed PR:** #93, OPEN / DRAFT / UNMERGED  
**Exact reviewed head:** f9834d29235738573ad773f19ebcc9b7c0f4c129  
**Exact-head CI:** Actions run 45020379946, conclusion SUCCESS  
**Review branch base:** PR #104 head 2ac31b1fa8ee69fc66df574ba6ccf94cd53d92ae

## Scope and limits

This is a bounded static review of the PR #93 uploader-memory follow-up and its tests. It is not an exhaustive audit, an independent security sign-off, a legal rights determination, or owner-device / real-media verification. No application code or tests are changed by this review. No OAuth credentials, tokens, real media, live upload, or publishing are used.

## Positive controls observed

- `validate_upload()` checks the configured positive byte ceiling before the CLI proceeds.
- `_copy_stream_with_limit()` enforces the ceiling while copying, so a source that grows after the initial stat cannot make the staged copy exceed the configured limit.
- The uploader hashes the exact immutable in-memory payload and supplies a stream over those same bytes to the YouTube client.
- OAuth subject, configured destination channel, per-clip/source/privacy/hash approval, and current publish rights are checked before request construction.
- PR #93 exact head `f9834d29235738573ad773f19ebcc9b7c0f4c129` is associated with Actions run [45020379946](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45020379946). Ubuntu job `137201721141` and hosted-Windows job `137201721314` completed successfully, including compilation, unit-test steps, and synthetic MP4/FFprobe validation. No numeric test count is asserted from the available metadata.

## Review findings

### R1. Incremental-copy regression does not exercise a multi-read growth case

**Classification:** Test coverage gap; no implementation defect established.

The current `test_snapshot_copy_stops_before_writing_bytes_over_limit` uses a `BytesIO(b"12345")` source with a four-byte limit. A normal read returns all five bytes at once, so the test proves rejection of an oversized first chunk, but does not prove that the copier accepts an initial in-budget chunk and rejects a later chunk that crosses the cumulative limit.

**Recommended follow-up test:** use a deterministic reader that returns an in-budget first chunk and an over-budget second chunk (for example, four bytes followed by one byte with a four-byte ceiling). Assert the second chunk is rejected, the accumulated snapshot never exceeds the configured limit, and the caller's temporary staging directory is cleaned up after the exception. Keep the test synthetic and offline.

### R2. Direct-call size guard lacks a focused regression

**Classification:** Test coverage gap; no bypass established in the normal CLI path.

`upload_video()` independently checks the configured limit before importing or invoking the Google API client. Existing new coverage directly exercises `validate_upload()` and the copy helper, but does not appear to assert that a caller invoking `upload_video()` directly with an oversized file is rejected before OAuth/API setup.

**Recommended follow-up test:** call `upload_video()` with a synthetic oversized file and a small configured limit; assert the size error and that Google API client construction, OAuth, and `videos().insert` are never reached. No network upload.

### R3. Source-rights re-registration can clear revocation

**Classification:** Previously recorded potential rights-reinstatement ambiguity; not a proven upload bypass.

The PR #93 source-rights registry still updates an existing `source_id` on conflict and sets `revoked_at=NULL`, while writing the audit action as `registered`. This finding is already recorded in the ARO-CHAT-0056 registry review. Preserve that lineage rather than treating it as a new discovery.

**Recommended owner decision:** confirm renewal/re-grant semantics. Before changing implementation, decide whether reinstatement requires a distinct explicit operation or grant/version identity, durable evidence, a separate audit action, and a regression proving ordinary duplicate registration cannot silently clear revocation.

## Disposition

- No new uploader bypass was established in this bounded static pass.
- R1 and R2 are focused test-coverage recommendations, not claims that the current implementation fails.
- R3 remains an unresolved owner/implementation-semantics question already recorded by ARO-CHAT-0056.
- Issue #68 remains OPEN / UNASSIGNED. Do not select, merge, close, retarget, or consolidate overlapping uploader/OIDC PRs based on this review.
- Keep live uploads and public publishing disabled pending owner assignment, canonical PR selection or approved consolidation, independent review, owner-device verification, authorized source media and permission evidence, real-media validation, and owner acceptance.
