# ARO-CHAT-0341 | Close smoke verifier descriptor when final fstat fails

- Exact title: ARO-CHAT-0341 | Close Smoke Verifier Descriptor When Final Fstat Fails.
- Workstream: ARO-GTA-P0-341.
- Continuation target: existing draft PR #386, existing branch and original base unchanged.
- Finding: the synthetic output verifier performs a second `os.fstat()` after hashing to confirm the opened file remained stable. Descriptor cleanup must still occur if this final descriptor metadata read raises `OSError`.
- Change: added `test_hash_verified_output_closes_descriptor_when_final_fstat_fails`. It captures the opened descriptor, allows the initial `fstat()`, injects an `OSError` on the final `fstat()`, and verifies the descriptor is closed by the helper's `finally` block. Production code unchanged.
- Test commit: `5a06dc067d551a32ca52ceaff98c3c07075c165b`.
- Tests NOT RUN in this connector session. Synthetic FFmpeg end-to-end NOT RUN. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED. Independent review NOT RECORDED. Owner-device Windows verification NOT VERIFIED. Authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and original branch/base. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
