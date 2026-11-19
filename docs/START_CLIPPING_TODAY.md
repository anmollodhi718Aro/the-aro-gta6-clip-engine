# Start clipping today

This is the shortest safe path from a local recording to reviewed MP4 clips. It does not require a cloud server or public upload.

## Before starting

You need:

- Windows, macOS or Linux with Python 3.11+.
- FFmpeg and ffprobe installed and available on PATH.
- A local recording that you created or are expressly authorized to edit and publish.
- Authorized chat-event data for that exact stream, exported in the input shape accepted by `backend.app.cli`.
- The measured UTC timestamp corresponding to media offset 0 in that exact local recording.

Do not use another creator's video or an official trailer unless you have the rights needed for the intended edits and distribution. Chat spikes only suggest moments; they do not prove that a moment is interesting.

## 1. Get the project

```powershell
git clone https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine.git
cd the-aro-gta6-clip-engine
git checkout integration/release-candidate
```

## 2. Check the local machine

```powershell
python --version
ffmpeg -version
ffprobe -version
```

Python must be 3.11 or newer. If FFmpeg or ffprobe is missing, install FFmpeg for your operating system and reopen the terminal so PATH refreshes.

## 3. Run the repository checks

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_project.ps1
```

This compiles the code and runs the full unittest suite. Do not continue as if the checks passed if this command reports an error.

## 4. Start the local Studio

```powershell
python THE_ARO_STUDIO.py
```

Open http://127.0.0.1:8765 in your browser. The Studio is local to this computer; it is not a hosted public dashboard.

## 5. Analyze authorized chat events

Prepare a JSON file with a permission record and chat events. Each event needs a stable event ID, source ID, timezone-aware timestamp and message text. The permission record must identify the same source and include the `analyze_chat` scope with a currently valid grant.

```powershell
python -m backend.app.cli .\my_authorized_chat.json --output .\clip_plan.json
```

The included `examples/sample_events.json` is synthetic test data only. It is useful for checking the analysis command, not for finding real highlights or clipping a real recording:

```powershell
python -m backend.app.cli .\examples\sample_events.json --output .\demo_clip_plan.json
```

## 6. Map candidates to the exact recording

Record the UTC time that corresponds to the first frame / media offset 0 of your local recording. Do not guess this value. Use the same source/recording represented by the chat events.

```powershell
python -m backend.app.clip_pack .\clip_plan.json --media-origin-utc "2026-11-19T00:00:00+00:00" --output-dir .\clip_pack
```

Replace the example timestamp with your measured timestamp. If the clock drifted during the stream, use at least three independently measured anchors from that same recording instead of a single origin:

```powershell
python -m backend.app.clip_pack .\clip_plan.json --clock-anchors-json .\my_measured_anchors.json --output-dir .\clip_pack
```

Open `clip_pack\clip_candidates.md` and inspect the CSV. The candidate offsets must line up with the actual moments in your recording.

## 7. Score and dry-run

```powershell
python -m backend.app.candidate_quality .\clip_pack\clip_candidates.csv --output .\clip_pack\quality_scored_candidates.csv
python -m backend.app.batch_render .\clip_pack\clip_candidates.csv --media "D:\\Videos\\my_authorized_recording.mp4" --approve 1 --output-dir .\rendered_clips
```

Replace the media path and row number. Dry-run is the default: it plans the selected row but does not render a video. Check the report and verify the exact source, timing and rights before rendering.

## 8. Render only the rows you personally approve

```powershell
python -m backend.app.batch_render .\clip_pack\clip_candidates.csv --media "D:\\Videos\\my_authorized_recording.mp4" --approve 1 --output-dir .\rendered_clips --execute --confirm-rights
```

The renderer probes the real media duration and blocks invalid/out-of-range candidates. Each execution uses a separate run folder. Open the generated report and watch every output clip before considering publication.

## 9. Current boundaries

- No automatic speech-to-text: Subtitle Studio formats a transcript you supply.
- No automatic visual highlight recognition: chat activity is the current candidate signal.
- No automatic sync-marker detection: the media origin or clock anchors must be measured by you.
- No automatic posting or scheduled publishing. The optional YouTube uploader requires separate Google OAuth setup and explicit human approval.
- No Instagram publishing workflow is enabled.
- A rendered clip is not cleared for upload until you review the edit, source permission, game/music/third-party rights, platform rules and audience declaration.

If you do not have authorized chat data yet, you can still edit your own recording manually in a video editor today; this engine's current automated candidate detector depends on chat-event input.
