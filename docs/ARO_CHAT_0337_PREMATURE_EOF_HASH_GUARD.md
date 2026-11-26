# Historical alias: premature EOF output-hash regression

This file was created with a provisional ARO-CHAT-0337 label before the concurrent registry was re-read. ARO-CHAT-0337 is canonically assigned to final-`lstat` descriptor cleanup. The premature-EOF regression is canonically registered as **ARO-CHAT-0339**, with report at `docs/ARO_CHAT_0339_PREMATURE_EOF_HASH_GUARD.md`.

No source or test commit was rewritten. The regression test is `test_hash_verified_output_rejects_unexpected_early_eof_and_closes_descriptor` in `tests/test_synthetic_single_clip_smoke.py`.
