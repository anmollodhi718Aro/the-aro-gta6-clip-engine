# ARO-CHAT-0340: restore discovery of final-lstat descriptor cleanup regression

- Exact title: ARO-CHAT-0340 | Restore Discovery of Final-lstat Descriptor Cleanup Regression.
- Workstream: ARO-GTA-P0-340.
- Continuation target: existing draft PR #386, branch `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`, original base unchanged.
- Finding: `test_hash_verified_output_closes_descriptor_when_final_lstat_fails` was indented beneath the module's `if __name__ == "__main__":` block, after `unittest.main()`. Standard unittest discovery imports the module with a different `__name__`, so the regression was not defined on the test class and was not discoverable.
- Fix: move the existing test method back into its test class, before the module's `unittest.main()` guard. Test logic and production code are unchanged.
- Test-file commit: `db95ef617def378b7be4127d859e37e01170208a`.
- Static source verification: the method now appears before the module guard and at test-class indentation. This is structural verification only, not an executed test result.
- Local unit tests NOT RUN. Synthetic FFmpeg end-to-end NOT RUN. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED. Independent review NOT RECORDED. Owner-device Windows verification NOT VERIFIED. Authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and original base/ancestry. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
