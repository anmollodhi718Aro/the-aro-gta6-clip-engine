# Start Clipping Today (Windows)

## Fastest path: one local recording, manually selected moments

1. Install Python 3.11+ and FFmpeg (including ffprobe), and make sure all three commands are available in a new terminal.
2. Download/clone this repository and open its folder.
3. Double-click `START_MANUAL_CLIPPING.bat`.
4. Choose landscape or vertical 9:16 Shorts/Reels output. Vertical mode preserves the full gameplay frame over a blurred background instead of cropping away the HUD or action.
5. Add up to 50 manually selected moments from the same recording. Each clip can be up to 180 seconds.
6. Enter the full path to a local recording you own or are authorized to edit and publish. The wizard checks the video stream and actual duration.
7. Inspect the dry-run summary. Type `RENDER`, then separately type `I CONFIRM RIGHTS`, only when you approve the exact recording and every selected range.
8. Open the resulting MP4 files and the generated read-only review dashboard in the session folder.

The wizard does not download videos, access private streams, upload, or publish. A local recording must be supplied by you. Game footage, music, overlays, and third-party content may have separate rights. Do not use another creator's recording without explicit permission covering editing and distribution.

## Studio dashboard

Double-click `START_THE_ARO_STUDIO.bat` or run `python THE_ARO_STUDIO.py`, then open http://127.0.0.1:8765. Keep the terminal open while using it.

## Troubleshooting

- If Python is missing, install Python 3.11+ and enable the Python launcher or Add Python to PATH.
- If FFmpeg/ffprobe is missing, install FFmpeg, add its `bin` folder to PATH, and reopen the terminal.
- If rendering fails, inspect the session report and confirm the selected range is inside the video duration.
- Nothing is automatically uploaded. Human review and a separate upload decision are always required.
