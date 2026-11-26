# One-selected-video clip render

This command is the single-file rendering stage after the owner-selected source passes FFprobe metadata preflight. It never scans a directory or processes multiple videos.

Dry-run (default):

```bash
python -m backend.app.single_clip_render "/path/to/one-authorized-video.mp4" --start 12.5 --end 27.0
```

The command validates the selected source, checks finite clip bounds, enforces the 180-second renderer limit, and confirms that the end time does not exceed the selected video's probed duration. Before inspecting or rendering media, it reserves the JSON report path exclusively. If the report already exists, or aliases the selected source/output path, the command stops before processing. The report is never overwritten. A `PLANNED` result does not create a video.

Actual local rendering requires both explicit flags:

```bash
python -m backend.app.single_clip_render "/path/to/one-authorized-video.mp4" --start 12.5 --end 27.0 --execute --confirm-rights
```

FFmpeg writes its intermediate MP4 inside a newly created private temporary directory on the destination filesystem. This avoids exposing an unreserved temporary filename in a shared output directory; the verified result is still published with an atomic no-overwrite hard link, and the private staging directory is removed afterward. The low-level renderer also rejects boolean clip bounds explicitly. Python treats booleans as integers, so values such as `True` must not silently become a one-second timestamp when the helper is called directly. The output is rendered locally through the existing collision-safe FFmpeg helper, then checked again with FFprobe. FFmpeg receives a duration-scaled timeout: at least 180 seconds, ten times the requested clip duration, and at most 1,800 seconds. This avoids imposing the same three-minute ceiling on a maximum-length clip rendered on a slower CPU, while retaining a finite upper bound. A successful render is still only a local artifact and requires manual playback/review. This command does not authenticate, upload, schedule, or publish.

Use only a source file that the owner has explicitly authorized for this processing scope. The confirmation flag is a workflow guardrail, not independent legal verification. Never use this command with scraped, ripped, or otherwise unapproved third-party media.


## Source snapshot safety

Before preflight, the CLI opens the one selected source without following symlinks where the platform supports `O_NOFOLLOW`, verifies that the opened descriptor and selected pathname identify the same regular file, and copies the source to a private temporary snapshot in bounded 1 MiB chunks. It rechecks descriptor metadata and pathname identity after the copy and rejects partial, replaced, or mutated sources. FFprobe and FFmpeg both consume that same snapshot, so the source bytes rendered are the bytes that passed preflight. The temporary snapshot is removed when the invocation ends. This uses temporary disk space proportional to the selected source size; it does not buffer the video in RAM or enumerate other files.


## Dry-run and rights-confirmation storage boundary

A dry-run probes the one selected source in place and does not create a duplicate video snapshot. If `--execute` is supplied without `--confirm-rights`, the command returns `BLOCKED` before opening or copying the source. Only an explicitly confirmed execution creates the private descriptor-verified snapshot used by both FFprobe and FFmpeg. The snapshot still uses temporary disk space proportional to the selected source size; it is not created for planning-only runs.

## Validate candidate output before reading source bytes

In candidate-CSV mode, the CLI reserves and fsyncs the RUNNING report first, then validates the selected output destination before hashing the complete source video against the trusted inventory digest. An existing output, symlink destination, invalid extension, or source/output alias therefore fails without a full-source hash read. The trusted digest check remains mandatory before FFprobe or rendering, and the renderer repeats destination validation at its own boundary. The regression test verifies that an existing output is preserved and neither source hashing nor rendering is invoked.

## Reject invalid output before copying the selected source

The execution path validates the requested output destination before creating the temporary source snapshot. Existing outputs, symbolic-link destinations, non-MP4 paths, and source/output aliases therefore fail without copying the selected video to temporary storage. The output is checked again by the lower-level renderer before FFmpeg is invoked, and final publication remains collision-safe.


## Path-resolution failures

Output and report path resolution fails closed. Symlink-loop and malformed-path resolution errors are reported as validation failures rather than escaping as uncaught exceptions; the CLI exits without leaving a reserved report file when path validation fails.


## Validate clip bounds before source snapshot

For confirmed execution, clip bounds are normalized and checked for finite numeric values, valid ordering, and the 180-second maximum before the selected source is copied to temporary storage. Invalid bounds therefore fail without snapshot I/O or FFprobe/FFmpeg invocation. The renderer repeats the same validation at its own boundary.


## Reject unrepresentable rendered-duration metadata

The post-render FFprobe duration must be a finite, positive numeric value. Extremely large integer metadata can raise `OverflowError` during `math.isfinite()`; malformed metadata now produces a deterministic `FAIL` report instead of an uncaught exception. The output is not marked `RENDERED`, and upload/publishing remain disabled.


## Selected-video preflight path identity

The standalone one-video FFprobe preflight checks the selected path with `lstat()` before and after probing. It rejects symlinks and non-regular files, compares path identity with followed-file metadata, and detects replacement while FFprobe is running. On POSIX it also compares change time so an in-place same-size mutation is rejected even if modification time is restored. Windows creation-time semantics are handled separately; hosted Windows CI is not owner-device verification.


## Unverified output cleanup

If FFprobe rejects a newly rendered clip or its duration is outside the requested
bounds, the renderer preserves the output and reports
`unverified_output_removed: false` and `manual_cleanup_required: true`.
A separate path identity check followed by `unlink()` is not atomic: another
process could replace the directory entry between those operations, causing
cleanup to delete a different file. The portable implementation therefore
does not automatically delete unverified output. Inspect the failed output
manually before removing it; existing destinations are never overwritten.


## Durable CLI execution reports

Before media inspection or rendering, the CLI exclusively creates and flushes a valid
`RUNNING` report. It records whether both execution and rights-confirmation flags
were supplied. If the process is forcibly terminated, that report remains a
parseable indication that the final outcome is unknown; inspect the destination
before retrying. If the renderer returns or raises a handled `OSError`,
`RuntimeError`, or `ValueError`, the CLI writes a terminal `FAIL` report with
the error and a manual-output-inspection warning instead of leaving a stale
`RUNNING` status. Upload and publishing fields remain false.


## Render one explicitly selected clip-pack row

A review-ready row can be handed to the single-clip CLI without manually
retyping its timestamps:

```bash
python -m backend.app.single_clip_render "/path/to/one-authorized-video.mp4" \
  --candidate-csv clip_pack/clip_candidates.csv --candidate-row 1
```

Candidate row numbers are one-based data rows; the CSV header is not counted.
The command reads exactly that row and requires `renderable=True`, a nonblank
source ID, finite start/end/duration values, valid renderer bounds, and duration
agreement within 50 ms. It records the selected row and source ID in the render
report. This is still a dry run by default. Actual rendering still requires
both `--execute` and `--confirm-rights` for the exact selected local source.
The source ID is traceability metadata, not proof that the local video is the
same source; the operator must verify that relationship before confirming
rights. The original `--start` and `--end` interface remains available, but
the two selection methods cannot be mixed.


## Candidate CSV structure validation

Candidate selection accepts UTF-8 CSV files with or without a byte-order mark, including common spreadsheet exports. Invalid UTF-8 byte sequences are reported as a controlled candidate-CSV validation error before report reservation, rather than escaping as a decoding traceback. The selected row is rejected if the header contains blank or duplicate column names, if required cells are missing, or if the row contains extra values beyond its header. These checks prevent ambiguous column mapping and malformed selected-row data. They do not establish that the operator's local video is the source identified by the CSV metadata.


## Clip-pack handoff regression coverage

The renderer test suite includes a cross-module check that writes a review-ready candidate with the clip-pack exporter, then loads the exact exported CSV row through the renderer's candidate selector. This protects the CSV schema boundary against accidental drift between the two stages. The test must still be executed in CI or a local Python environment before the handoff is considered validated.


The cross-module regression test exercises the preceding measured timestamp mapping function as well as CSV export and renderer selection. It verifies that the mapped source ID and media offsets survive the full metadata handoff. Execution of this test suite is still required before treating the integration as validated.


### CLI candidate-selection regression

A CLI-level regression covers the complete metadata handoff from measured candidate mapping through clip-pack CSV export to renderer invocation using `--candidate-csv` and `--candidate-row`. It asserts the selected timestamps reach the renderer and the JSON report retains the exact source ID and selected row number. The test uses a mocked renderer in dry-run mode; it does not execute FFmpeg or validate real media.


### Candidate source confirmation

When selecting a clip-pack row from the CLI, provide `--source-id` with the same source ID as the selected CSV row. The CLI rejects a missing or mismatched value before reserving the render report or inspecting media. This is an explicit operator cross-check intended to catch accidental selection of a candidate row from another source. It is **not** cryptographic or automatic proof that the selected local file corresponds to that source ID; operators must independently verify the selected file against their authorized source record.


### Trusted source digest confirmation

Candidate CSV CLI mode also requires `--source-sha256`. Supply the expected 64-character SHA-256 digest from the trusted authorized-media inventory, not a digest calculated from an unverified copy at the moment of invocation. The CLI first checks the selected local file through a non-following descriptor. For confirmed rendering, the expected digest is also calculated while copying from the verified source descriptor into the private snapshot. The digest is compared before FFprobe or FFmpeg can consume that snapshot, so the comparison applies to the exact bytes used by both tools. A mismatch, malformed digest, symlink, or detected file change fails closed. The render report records the digest of the verified snapshot. Dry-run remains non-copying; its initial digest check is an inventory cross-check, not a guarantee against later file changes. This check binds the chosen bytes to the trusted inventory digest; it does not establish who created the file or grant processing rights. The rights confirmation gate remains separate.


### Terminal report serialization safety

The CLI fully serializes the terminal JSON report in memory before seeking to or truncating the exclusively reserved report file. If serialization fails, the existing newline-terminated `RUNNING` reservation is preserved for manual review instead of being partially overwritten. This does not make subsequent filesystem writes atomic: an I/O failure during the final write or hard process termination can still leave an incomplete report. Treat any non-terminal or unreadable report as an unknown outcome and inspect the output manually before retrying. A report-write failure never authorizes deleting or overwriting a rendered output.


The CLI prints the same pre-serialized terminal JSON string that it writes to the report file. It does not serialize the report a second time after the durable write, avoiding a second serialization failure or stdout/file representation drift.


### Partial terminal report write recovery

A terminal report filesystem write can fail after truncation has begun, leaving the report unreadable even when rendering already completed. The CLI returns a report-write error; that error does **not** establish that rendering failed. Preserve any output file and inspect it manually before retrying or cleaning up. The regression test injects a partial report write after a mocked successful render and verifies that the output bytes are preserved. This test is a failure-mode contract, not proof of filesystem atomicity or real-media correctness.


If writing the reserved report fails after the terminal JSON has been serialized, the CLI attempts an exclusive-create sidecar named `<report>.terminal-fallback.json`. It never overwrites an existing sidecar. A successful sidecar write is flushed and fsynced; the CLI still returns an error because the primary report may be partial. If the sidecar already exists or cannot be written, both errors are reported and manual inspection remains required. This fallback is not a transaction or a guarantee against power loss, filesystem faults, or partial sidecar writes.

The fallback path is also resolved and checked against the selected source and output paths before creation. If it aliases either protected path, fallback creation is refused rather than placing a report where source media or render output belongs.

The fallback writer also checks the text stream's reported character count. A short write is treated as a failed fallback, not as a complete recovery record. The exclusive sidecar may remain incomplete after such a failure; do not overwrite or delete it automatically. Inspect the primary report, sidecar, and any output manually.

The initial `RUNNING` reservation is serialized fully before writing. Its write count is checked, then flushed and fsynced before any media inspection. If the initial write fails or is short, the CLI attempts the same exclusive sidecar recovery and stops before calling the renderer. A fallback containing `RUNNING` means no media processing was started by this invocation; inspect the primary reservation and fallback before retrying.

Terminal report replacement also verifies the write character count before truncating the old reservation. A short write is treated as failure and triggers exclusive fallback recovery, rather than being accepted as a completed terminal report. This check does not make the in-place update atomic against power loss or filesystem faults.


### Report newline encoding correction
The initial and terminal report payloads, plus the exclusive fallback writer, use actual newline characters rather than literal backslash-plus-n text. This keeps the report valid JSON with a conventional trailing newline. A regression test checks both the trailing newline and successful JSON parsing of the fallback payload.


### Unexpected exceptions after snapshot verification

If FFprobe/FFmpeg or a later render step raises after the selected source has been copied and its digest verified, the terminal FAIL report retains `source_snapshot_created=true`, `source_snapshot_verified=true`, and the verified `source_sha256`. The processing-start state is marked unknown when the exception does not establish whether FFmpeg began. If the CLI itself receives an unexpected exception before it gets a structured renderer result, snapshot fields are null (unknown), not false. Inspect any output before retrying.


### Temporary snapshot cleanup failure

If temporary-directory cleanup raises after snapshot creation, the terminal
failure report retains `source_snapshot_created=true`, the verified snapshot
SHA-256, and `source_snapshot_verified=true`. If a structured render result
was already returned, its known processing state and preflight evidence are
preserved. The command reports `FAIL` because temporary cleanup did not
complete; inspect the output and temporary files manually before retrying.
Upload and publishing remain disabled. A cleanup failure is not evidence that
rendering never started or that an already-created output is absent.


### Conservative processing-start reporting

The renderer does not mark `processing_started=true` merely because it entered
the lower-level `render_clip()` function. That function performs additional
path and bounds validation before launching FFmpeg. The report therefore keeps
the state unknown while that call is in progress and sets it true only after
`render_clip()` returns successfully. If the call raises, the report does not
claim that processing started when the exact subprocess state is unavailable.


## Fail closed on incomplete source snapshot writes

Every bounded source-snapshot chunk must be fully written before its bytes are
included in the snapshot digest and copied-byte count. A short write raises an
I/O failure immediately, and the snapshot helper removes only the partial file
created by that invocation after verifying its file identity. It never reports
a digest for a partially written snapshot as though the complete source had
been copied. The selected original remains untouched.


## Verify persisted source snapshot bytes

After the snapshot writer flushes and syncs the file, the renderer reopens the
created snapshot through a non-following, nonblocking read descriptor and hashes
the bytes read back from storage. Nonblocking open prevents an unexpected FIFO
or device replacement from hanging verification before descriptor type checks. It checks the snapshot file identity and size before
reading, then checks descriptor/path identity and metadata again afterward.
The persisted-byte digest must match the digest of the selected source bytes.
A mismatch fails closed and triggers identity-checked cleanup of the partial or
untrusted snapshot. This verifies the bytes actually readable from the snapshot,
not merely the buffers passed to the writer.


## Final rendered-output integrity evidence

After FFprobe and duration validation, the renderer hashes the output bytes
through a non-following read descriptor. It verifies regular-file identity,
size, modification/change metadata, and path identity before and after the
read. The metadata captured immediately after FFmpeg must still match after
FFprobe, preventing a post-probe replacement or mutation from being reported
as a verified render. A successful report includes `output_sha256`,
`output_size_bytes`, and `output_identity_verified=true`. If final verification
fails, the report is FAIL, hash/size are null, and the output is preserved for
manual inspection rather than automatically deleted.


### Selected-source inventory hashing: nonblocking open

Candidate-mode source SHA-256 verification now requests nonblocking descriptor open where the platform supports it. This closes a lstat-to-open race in which a replaced FIFO or device could otherwise block the hashing process before descriptor type validation. The descriptor is still required to identify a regular non-symlink file. Regression coverage checks the open flags on platforms exposing O_NONBLOCK. This is a defensive path-race guard, not proof of media ownership or processing rights.


## ARO-CHAT-0302 — candidate dry-run digest binding

Candidate CSV dry-run mode now re-hashes the selected source after FFprobe preflight and verifies that the file identity still matches the identity observed across preflight. The resulting SHA-256 must match the trusted inventory digest supplied for the selected candidate row. This closes a gap where the CLI's initial digest check could be followed by a path replacement before dry-run metadata inspection, producing a plan whose candidate identity and probed media did not refer to the same bytes. The hash reader also counts the bytes actually returned by the descriptor and requires that count to equal the descriptor's stable file size; an early EOF or incomplete read therefore fails closed instead of accepting a digest of only a prefix.

The dry-run remains read-only with respect to media: it does not create a full source snapshot, invoke FFmpeg, or render output. Added regressions for digest mismatch and successful digest evidence. Tests have not yet been run in this continuation; exact-head CI and independent review remain pending.


## ARO-CHAT-0304 — reserve the run report before candidate media hashing

Candidate-CSV mode now validates the trusted SHA-256 argument and selected row metadata before report reservation, but it does not read the selected media bytes until after the exclusive RUNNING report has been written and flushed. This keeps candidate hashing, like FFprobe and rendering, behind the durable run record. A hash-open/read failure or digest mismatch is recorded as a terminal FAIL report and does not invoke the renderer. The selected digest is retained in the terminal candidate-selection metadata only after it matches the trusted inventory value.

Added a CLI regression that inspects the report from inside the source-hash callback and requires it to contain a parseable RUNNING record before the hash begins. Tests have not been run in this connector session; exact-head Ubuntu/hosted-Windows CI and independent review remain unverified. No real media is processed by this change.


### Execution-request reporting clarification
The reserved in-progress JSON report records `execution_requested` from the explicit `--execute` flag alone and records `rights_confirmation_supplied` separately from `--confirm-rights`. This keeps a blocked attempt distinguishable from a dry-run: requesting execution without rights confirmation is reported as requested-but-blocked, never as a dry-run. This is reporting only; the existing fail-closed rights gate is unchanged.


The terminal JSON report retains the reserved invocation metadata and overlays the renderer's terminal result. This ensures the execution-request and rights-confirmation fields remain present after a BLOCKED, PLANNED, RENDERED, or FAIL result is written.


### Snapshot read-back completeness

After the private source snapshot is flushed and fsynced, read-back verification now counts the bytes actually returned by descriptor reads and requires the count to equal the stable snapshot size. An injected or abnormal early EOF fails closed and triggers identity-checked cleanup of the snapshot created by this invocation. This complements the SHA-256 comparison by making complete read coverage an explicit invariant.


## Terminal fallback path normalization
The CLI expands the configured report path before reserving it. If terminal JSON persistence later fails, the exclusive `.terminal-fallback.json` file is created beside that same expanded report path. This is important for paths beginning with `~`: the fallback must not be written to a literal tilde-prefixed relative path. The regression test forces a short terminal write and checks that fallback creation receives the expanded path.


## Snapshot cleanup failure reporting

If source snapshot creation fails after creating its temporary file and identity-checked cleanup cannot be confirmed, the renderer returns FAIL with source_snapshot_created=true, source_snapshot_verified=false, and source_snapshot_cleanup_required=true. The report does not claim a verified source digest. Inspect the temporary workspace before retrying. A path whose identity changed is preserved rather than unlinked.


## Preserve valid JSON for unusual filesystem names

Filesystem paths can contain surrogate-escaped characters when a POSIX filename
contains bytes that are not valid UTF-8. JSON reports are serialized with
ASCII escaping so those path values are represented as valid UTF-8 JSON rather
than raising an encoding error during the durable RUNNING or terminal report
write. Reading the report with a JSON parser restores the original escaped
string value. This does not change the selected path or media bytes.


### ARO-CHAT-0308 — fallback regression trigger correction
The end-to-end fallback regression injects a short write on the second write to the reserved primary report handle. The first write persists the RUNNING record; the second attempts the terminal report. This causes the test to exercise exclusive fallback-file creation instead of leaving the fallback path untested. This is test-only and does not change renderer or report-writing behavior. The test has not been run in this connector session.


## Standards-compliant JSON and finite CLI bounds

The CLI rejects NaN and positive/negative infinity in direct `--start` or
`--end` arguments before reserving a report or inspecting media. Python's
argument parser accepts these spellings as floats, but JSON does not permit
non-finite numeric literals. Initial and terminal reports are serialized with
non-finite JSON values disabled, so malformed media-tool metadata cannot silently
produce a report that a strict JSON parser rejects. A rejected bound creates no
report and starts no media operation.

## Rendered MP4 format and video-codec verification

A post-render FFprobe `PASS` and matching duration are not sufficient by themselves. The output must also identify an MP4-compatible container, contain a video stream encoded as H.264, and report positive integer width and height. A mismatch produces `FAIL`; the output is preserved for manual inspection, and upload/publishing remain disabled. This gate validates the rendered file's reported container and video stream metadata, not visual quality or owner playback acceptance.


## Terminal fallback path-resolution failures

If a terminal report write fails, the CLI attempts an exclusive fallback file beside the reserved report. Resolution of the fallback and protected source/output paths is itself guarded: malformed paths and symlink-loop errors are converted into the fallback's normal I/O failure path. The CLI then emits the explicit warning to inspect any output manually before retrying. It never overwrites an existing fallback or protected file. A failed fallback does not prove that rendering failed; inspect the output and both report paths before another attempt.

The MP4/H.264 post-render gate also rejects missing video streams, missing or non-positive dimensions, and boolean dimension metadata. Direct helper regressions cover acceptance of a valid H.264 MP4 stream and each malformed metadata class. See `docs/ARO_CHAT_0311_RENDERED_MP4_METADATA_REGRESSIONS.md`; these tests have not yet been executed in this connector session.
