# Start clipping from a local recording today

This is the quickest path when you already have a local recording but do not yet have a synchronized chat export or YouTube API setup.

## One-click Windows start

1. Install Python 3.11+ and FFmpeg (including ffprobe).
2. Clone the repository and open its folder in File Explorer.
3. Double-click `START_MANUAL_CLIPPING.bat`.
4. Wait for the source compilation and full Python test suite to pass.
5. Enter the full path to your authorized local recording.
6. Enter start/end offsets in seconds and an optional note.
7. Review the dry-run. Type exactly `RENDER` only when you approve the range and have permission to edit and publish that exact recording.

The launcher checks Python 3.11+, FFmpeg, ffprobe, Python compilation, and the complete unittest suite before opening the wizard. A failed check stops the workflow before rendering. The wizard validates the selected file and range, creates a unique session folder, runs a dry-run, and requires the explicit `RENDER` confirmation. Outputs remain local; there is no download, upload, or automatic publishing.

## Manual command-line workflow

### 1. Prepare a manual time-range file

Copy `examples/manual_clips.example.json` to `my_clips.json`. Replace the example offsets with times you selected by watching your own authorized recording. Offsets are seconds from the beginning of that exact file. Keep every range between 0 and 180 seconds long.

### 2. Create a render-review CSV

```bash
python -m backend.app.manual_clip my_clips.json --output manual_clips.csv
```

### 3. Dry-run the selected rows

```bash
python -m backend.app.batch_render manual_clips.csv \
  --media "/absolute/path/to/your-authorized-recording.mp4" \
  --approve 1 \
  --output-dir rendered_clips
```

Dry-run does not render. Inspect the report and confirm the selected time range is correct.

### 4. Render the approved local clip

Only after confirming you own or have permission to process the exact file:

```bash
python -m backend.app.batch_render manual_clips.csv \
  --media "/absolute/path/to/your-authorized-recording.mp4" \
  --approve 1 \
  --output-dir rendered_clips \
  --execute --confirm-rights
```

The command checks the actual video stream and duration with ffprobe. Each run uses a new folder and refuses to overwrite existing clips. Review the resulting MP4 before any distribution. No upload or automatic publishing occurs.

## Important

- The example offsets are placeholders, not actual GTA 6 moments.
- This manual path does not require chat data, API keys, OAuth, or internet access.
- For clips selected by chat spikes, use the separate measured-clock pipeline instead.
- Only process footage you own or are explicitly authorized to edit and distribute.
- Game publisher, music, guest, and other embedded third-party rights may need separate review.
