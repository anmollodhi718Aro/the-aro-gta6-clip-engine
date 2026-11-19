# First Clip Today — Windows Quick Start

This is the shortest safe path from a fresh clone to a reviewed local clip. Use only media you created or are explicitly authorized to edit and publish.

## Fastest Windows path: guided first-clip wizard

After installing Python 3.11+ and FFmpeg (including ffprobe), double-click `START_FIRST_CLIP.bat` in the repository folder. You can also run this from PowerShell at the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/first_clip.ps1
```

The wizard checks the Python version, verifies that the selected local file contains a readable video stream, reads its actual duration, and validates your manually selected start/end offsets (maximum 180 seconds). It creates a unique session, prepares a candidate CSV, and runs a no-render dry run first. Rendering requires two separate confirmations. The finished MP4 and review report remain local; nothing is downloaded, uploaded, or published automatically.

## One-time setup

Install Python 3.11 or newer and FFmpeg (including ffprobe). Open PowerShell in the cloned repository folder and verify:

```powershell
py -3.11 --version
ffmpeg -version
ffprobe -version
```

If the Python launcher is unavailable, make sure `python` on PATH is Python 3.11 or newer. The wizard checks both options.

## Optional project checks

Before using the project, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_project.ps1
```

Do not proceed if compilation or unit tests report an error. GitHub Actions currently has an external runner-allocation issue on this private repository, so a failed job with no runner and no steps is not a passing test result.

## What you need for the first clip

- A local video recording you own or have explicit permission to edit and distribute.
- A moment you have manually selected by watching that recording.
- Start and end offsets in seconds, measured from the beginning of that exact file.
- FFmpeg and ffprobe installed and available on PATH.

The wizard does not infer highlights from video or chat. It renders the time range you choose. Do not use another creator's VOD or stream without explicit permission covering editing and publishing on the intended platform. Game publisher, music, guest and other embedded third-party rights may need separate clearance.

## Output locations

- Session JSON, candidate CSV, dry-run report, render report and review HTML: `aro_studio_data/manual_sessions/`
- Rendered MP4 files: unique run folders under `rendered_clips/`

Open the review HTML and inspect the MP4 before sharing. A rendered clip is not automatically approved for publication.
