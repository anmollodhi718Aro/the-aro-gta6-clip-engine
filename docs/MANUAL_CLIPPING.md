# Start clipping from a local recording today

This is the quickest path when you already have a local recording but do not yet have a synchronized chat export or YouTube API setup.

## Windows one-click path

1. Install Python 3.11+ and FFmpeg (including ffprobe), then reopen Command Prompt.
2. Double-click `START_CLIPPING_TODAY.bat` in the repository folder.
3. Paste the full path to your own or explicitly authorized local video.
4. Enter each clip's start and end offsets in seconds, measured from the beginning of that exact file. Each clip is limited to 180 seconds and each session supports up to 50 clips.
5. After the final range, inspect the dry-run report for every row. Type `RENDER` only if you approve every listed range and have rights to edit and distribute that exact recording.

The wizard creates a unique session folder under `manual_clip_sessions/` containing the input JSON, CSV, and render reports/outputs. It renders locally only after the explicit confirmation. It does not download, upload, or publish video.

## Manual cross-platform path

### 1. Prepare a manual time-range file

Copy `examples/manual_clips.example.json` to `my_clips.json`. Replace the example offsets with times you selected by watching your own authorized recording. Offsets are seconds from the beginning of that exact file. Keep every range between 0 and 180 seconds long, with no more than 50 ranges per input file.

### 2. Create a render-review CSV

```bash
python -m backend.app.manual_clip my_clips.json --output manual_clips.csv
```

### 3. Dry-run the selected rows

```bash
python -m backend.app.batch_render manual_clips.csv \
  --media "/absolute/path/to/your-authorized-recording.mp4" \
  --approve 1,2 \
  --output-dir rendered_clips
```

Replace the media path and row numbers with the exact candidates you reviewed. Dry-run does not render. Inspect the report and confirm every selected time range is correct.

### 4. Render the approved local clips

Install FFmpeg and ffprobe, then run only after confirming you own or have permission to process the exact file:

```bash
python -m backend.app.batch_render manual_clips.csv \
  --media "/absolute/path/to/your-authorized-recording.mp4" \
  --approve 1,2 \
  --output-dir rendered_clips \
  --execute --confirm-rights
```

The command checks the actual video stream and duration with ffprobe. Each run uses a new folder and refuses to overwrite existing clips. Review every resulting MP4 before any distribution. No upload or automatic publishing occurs.

## Important

- The example offsets are placeholders, not actual GTA 6 moments.
- This path does not require chat data, API keys, OAuth, or internet access.
- For clips selected by chat spikes, use the separate measured-clock pipeline instead.
- Only process footage you own or are explicitly authorized to edit and distribute.
