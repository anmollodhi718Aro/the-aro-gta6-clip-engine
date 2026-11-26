# ARO-CHAT-0305 — Validate candidate output before source hashing

- Chat ID: ARO-CHAT-0305
- Workstream ID: ARO-GTA-P1-305
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Existing PR: #386
- Existing branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Scope: one bounded CLI ordering correction; reuse the existing branch and PR.

## Finding

Candidate-CSV mode reserved its durable RUNNING report, then hashed the complete selected source against the trusted inventory digest, and only afterward entered the renderer where output-destination validation occurred. If the output already existed, was a symlink, used an invalid extension, or aliased the source, the CLI performed an avoidable full-source read before discovering that rendering could not proceed.

## Change

- Keep candidate metadata, source-ID, and trusted-digest syntax validation before report reservation.
- Preserve the exclusive RUNNING report reservation, flush, and fsync before any selected-media byte reads.
- After reservation, validate the selected output destination before candidate source hashing.
- On invalid destination, write a terminal FAIL report without hashing source bytes or invoking the renderer.
- Preserve the existing destination bytes; no overwrite or cleanup is attempted.
- Keep trusted source SHA-256 verification mandatory before FFprobe/rendering when the destination is valid.
- Add a regression proving an existing output is preserved and neither source hashing nor rendering is invoked.
- Update operator documentation.

## Commits

- Production: `d570401b19f8a0674e736815f298d02b925a36e4`
- Regression: `09ea69e31d3b461f27942eb6ce1eb051bd8072e8`
- Operator documentation: `95c132cfd85739918c184b19fab074aefac6a9d5`

## Validation

- Local repository tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED; no workflow runs or combined status entries were returned for the current head at inspection.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Real authorized MP4: NOT PROCESSED / NOT VERIFIED.
- The regression is added but has not been executed; do not claim it passed.

## Safety and scope

- Existing PR #386 remains OPEN / DRAFT / UNMERGED.
- Preserve its existing base and ancestry; no merge, rebase, retarget, or integration.
- No workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, or deployment.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Live uploads and public publishing remain disabled.
