# Start clipping from a local recording today

This is the quickest path when you already have a local recording but do not yet have a synchronized chat export or YouTube API setup.

## Windows one-click path

1. Install Python 3.11+ and FFmpeg (including ffprobe), and make sure both are available on PATH.
2. From the repository folder, double-click `START_MANUAL_CLIPPING.bat`.
3. Enter the full path to your authorized local recording.
4. Enter the start and end offsets in seconds, measured from the beginning of that exact file. Each clip must be 180 seconds or shorter.
5. Inspect the dry-run report. Type `RENDER` only when you have checked the range and own or have permission to edit and publish that exact recording.

The wizard creates a unique folder under `manual_clip_sessions/`, prepares a review CSV, checks the real video stream and duration with ffprobe, and renders locally only after the explicit confirmation. It never downloads footage, uploads clips, or publishes anything. The command window stays open so you can read the result.

## 1. Prepare a manual time-range file (cross-platform)

Copy `examples/manual_clips.example.json` to `my_clips.json`. Replace the example offsets with times you selected by watching your own authorized recording. Offsets are seconds from the beginning of that exact file. Keep every range between 0 and 180 seconds long.

## 2. Create a render-review CSV

```bash
python -m backend.app.manual_clip my_clips.json --output manual_clips.csv
```

## 3. Dry-run the selected rows

```bash
python -m backend.app.batch_render manual_clips.csv \\
  --media "/absolute/path/to/your-authorized-recording.mp4" \\
  --approve 1 \\
  --output-dir rendered_clips
```

Dry-run does not render. Inspect the report and confirm the selected time range is correct.

## 4. Render the approved local clip

Install FFmpeg and ffprobe, then run only after confirming you own or have permission to process the exact file:

```bash
python -m backend.app.batch_render manual_clips.csv \\
  --media "/absolute/path/to/your-authorized-recording.mp4" \\
  --approve 1 \\
  --output-dir rendered_clips \\
  --execute --confirm-rights
```

The command checks the actual video stream and duration with ffprobe. Each run uses a new folder and refuses to overwrite existing clips. Review the resulting MP4 before any distribution. No upload or automatic publishing occurs.

## Windows PowerShell example

```powershell
Copy-Item examples/manual_clips.example.json my_clips.json
notepad my_clips.json
python -m backend.app.manual_clip my_clips.json --output manual_clips.csv
python -m backend.app.batch_render manual_clips.csv --media "D:\\Videos\\authorized-recording.mp4" --approve 1 --output-dir rendered_clips
```

After inspecting the dry-run report, repeat the final command with `--execute --confirm-rights` to render.

## Important

- The example offsets are placeholders, not actual GTA 6 moments.
- This path does not require chat data, API keys, OAuth, or internet access.
- For clips selected by chat spikes, use the separate measured-clock pipeline instead.
- Only process footage you own or are explicitly authorized to edit and distribute.
