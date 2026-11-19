# First Clip Today — Windows Quick Start

**Fastest route: use a local recording and manually select clip timestamps.** This path needs no YouTube API key, OAuth, chat export, or cloud service.

Use only gameplay footage you recorded or are explicitly authorized to edit and distribute.

## Fast path: manual local clipping

1. Open your authorized recording in a video player/editor and note start/end offsets in seconds from the beginning of that exact file. Each range must be 180 seconds or shorter.
2. Copy and edit the sample input:

```powershell
Copy-Item examples/manual_clips.example.json my_clips.json
notepad my_clips.json
```

3. Generate the review CSV:

```powershell
py -3 -m backend.app.manual_clip my_clips.json --output manual_clips.csv
```

If `py` is unavailable, use `python` instead. The launcher requires Python 3.11 or newer.

4. Preview safely (replace the media path and approve only the row you reviewed):

```powershell
py -3 -m backend.app.batch_render manual_clips.csv --media "D:\Videos\your-recording.mp4" --approve 1 --output-dir rendered_clips
```

Dry-run is the default. Inspect the report and verify the exact time range and media file.

5. Render only after confirming rights for this exact recording and intended distribution:

```powershell
py -3 -m backend.app.batch_render manual_clips.csv --media "D:\Videos\your-recording.mp4" --approve 1 --output-dir rendered_clips --execute --confirm-rights
```

The renderer requires FFmpeg/ffprobe, checks the actual video stream and duration, writes to a unique run folder, and refuses to overwrite. Review the resulting MP4 before any separate upload decision.

For more detail, see [Manual Clipping](MANUAL_CLIPPING.md).

## Optional: chat-assisted workflow

The remaining steps below are for authorized chat-event analysis and manually measured synchronization. They are not required for the manual path above.

This is the shortest safe path from a fresh clone to a reviewed vertical clip. Use only media you created or are explicitly authorized to edit and publish.

## 0. One-time setup

Install Python 3.11 or newer and FFmpeg (including ffprobe). Open PowerShell in the cloned repository folder.

```powershell
py -3 --version
ffmpeg -version
ffprobe -version
```

If py is unavailable but python works, replace py with python below.

## 1. Validate the project

```powershell
py -3 -m compileall -q backend tests THE_ARO_STUDIO.py
py -3 -m unittest discover -s tests -v
```

Do not proceed if either command reports an error. Save the final test summary and commit SHA.

## 2. Start the local Studio

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_studio.ps1
```

The launcher selects Python 3.11+ and binds the dashboard to 127.0.0.1. Keep the PowerShell window open. You can also start it directly with `py -3 -m THE_ARO_STUDIO`.

Open http://127.0.0.1:8765. Keep the terminal open while using the dashboard. The dashboard is local-only.

## 3. Create candidate timestamps

The analyzer accepts authorized chat-event data. The repository sample is synthetic test data only, not a real GTA stream or permission for real footage.

```powershell
py -3 -m backend.app.cli path\to\your_authorized_chat_events.json --output clip_plan.json
```

The input must contain a valid permission grant for chat analysis and timestamped events. Results are candidate moments, not guaranteed highlights.

## 4. Align candidates to your recording

Measure the UTC timestamp corresponding to the start of the exact local recording. Never guess it.

```powershell
py -3 -m backend.app.clip_pack clip_plan.json --media-origin-utc "2026-11-19T12:00:00+00:00" --output-dir clip_pack
```

Replace the example timestamp with the measured value for your recording. For clock drift, use at least three manually verified anchors from that same recording:

```powershell
py -3 -m backend.app.clip_pack clip_plan.json --clock-anchors-json path\to\your_measured_anchors.json --output-dir clip_pack
```

Inspect clip_pack\clip_candidates.md. A mapped timestamp is not proof that a moment is useful.

## 5. Score and dry-run

```powershell
py -3 -m backend.app.candidate_quality clip_pack\clip_candidates.csv --output clip_pack\quality_scored_candidates.csv
py -3 -m backend.app.batch_render clip_pack\clip_candidates.csv --media "D:\Videos\your_authorized_recording.mp4" --approve 1,2 --output-dir rendered_clips
```

Change the media path and approved row numbers. Dry-run is the default. Inspect the report before rendering.

## 6. Render approved rows

Only after confirming you have rights to edit and publish this exact media:

```powershell
py -3 -m backend.app.batch_render clip_pack\clip_candidates.csv --media "D:\Videos\your_authorized_recording.mp4" --approve 1,2 --output-dir rendered_clips --execute --confirm-rights
```

The renderer probes actual media duration and blocks invalid bounds. Outputs go into a unique run folder under rendered_clips.

## 7. Review

Find the newest run folder under rendered_clips, then:

```powershell
py -3 -m backend.app.review_dashboard rendered_clips\RUN_ID\batch_render_report.json --output rendered_clips\review.html
```

Replace RUN_ID with the actual folder name. Open review.html and inspect exported clips before any upload.

## Important boundaries

- Chat APIs do not supply video files. This workflow does not download or rip livestreams.
- Do not use another creator's VOD or stream without explicit permission covering editing and publishing on the intended platform.
- Game publisher, music, guest and other embedded third-party rights may need separate clearance.
- No clip is uploaded or published automatically. Human review and approval remain required.
- Chat spikes and heuristic scores do not guarantee good clips, views, or monetization.
- If you have only a local recording and no authorized chat export, select moments in your editing software instead. Do not fabricate timestamps or claim the detector analysed the video.
