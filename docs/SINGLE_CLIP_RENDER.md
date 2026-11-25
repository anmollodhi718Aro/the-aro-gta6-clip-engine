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

FFmpeg writes its intermediate MP4 inside a newly created private temporary directory on the destination filesystem. This avoids exposing an unreserved temporary filename in a shared output directory; the verified result is still published with an atomic no-overwrite hard link, and the private staging directory is removed afterward. The low-level renderer also rejects boolean clip bounds explicitly. Python treats booleans as integers, so values such as `True` must not silently become a one-second timestamp when the helper is called directly. The output is rendered locally through the existing collision-safe FFmpeg helper, then checked again with FFprobe. A successful render is still only a local artifact and requires manual playback/review. This command does not authenticate, upload, schedule, or publish.

Use only a source file that the owner has explicitly authorized for this processing scope. The confirmation flag is a workflow guardrail, not independent legal verification. Never use this command with scraped, ripped, or otherwise unapproved third-party media.


## Source snapshot safety

Before preflight, the CLI opens the one selected source without following symlinks where the platform supports `O_NOFOLLOW`, verifies that the opened descriptor and selected pathname identify the same regular file, and copies the source to a private temporary snapshot in bounded 1 MiB chunks. It rechecks descriptor metadata and pathname identity after the copy and rejects partial, replaced, or mutated sources. FFprobe and FFmpeg both consume that same snapshot, so the source bytes rendered are the bytes that passed preflight. The temporary snapshot is removed when the invocation ends. This uses temporary disk space proportional to the selected source size; it does not buffer the video in RAM or enumerate other files.


## Dry-run and rights-confirmation storage boundary

A dry-run probes the one selected source in place and does not create a duplicate video snapshot. If `--execute` is supplied without `--confirm-rights`, the command returns `BLOCKED` before opening or copying the source. Only an explicitly confirmed execution creates the private descriptor-verified snapshot used by both FFprobe and FFmpeg. The snapshot still uses temporary disk space proportional to the selected source size; it is not created for planning-only runs.

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

Candidate selection accepts UTF-8 CSV files with or without a byte-order mark, including common spreadsheet exports. The selected row is rejected if the header contains blank or duplicate column names, if required cells are missing, or if the row contains extra values beyond its header. These checks prevent ambiguous column mapping and malformed selected-row data. They do not establish that the operator's local video is the source identified by the CSV metadata.


## Clip-pack handoff regression coverage

The renderer test suite includes a cross-module check that writes a review-ready candidate with the clip-pack exporter, then loads the exact exported CSV row through the renderer's candidate selector. This protects the CSV schema boundary against accidental drift between the two stages. The test must still be executed in CI or a local Python environment before the handoff is considered validated.
