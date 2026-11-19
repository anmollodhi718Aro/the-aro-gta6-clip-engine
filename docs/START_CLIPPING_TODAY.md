# Start clipping today (Windows)

This quick start renders a short clip from a local recording you own or are authorized to edit. It does not download streams, scrape platforms, upload, or publish.

## 1. Check prerequisites

Install Python 3.11+ and FFmpeg. Open a new PowerShell window and verify:

```powershell
py --version
ffmpeg -version
ffprobe -version
```

If `ffmpeg` or `ffprobe` is not recognized, install FFmpeg and add its `bin` folder to PATH, then reopen PowerShell.

## 2. Get the project

If you already cloned this repository, open PowerShell in its folder. Otherwise:

```powershell
git clone https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine.git
Set-Location the-aro-gta6-clip-engine
```

For the first run, use the clipping-MVP pull request branch only after it has been merged or check out its branch explicitly.

## 3. Create your permission record

Copy `examples/permission.render.example.json` to `permission.json`. Replace the source ID and attestation text with details for the exact recording. Do not claim rights you do not have.

## 4. Render your first clip

Replace the paths and timestamps below with your own local recording and the moment you selected:

```powershell
py -m backend.app.clip_cli "D:\Videos\my-authorized-recording.mp4" "D:\Videos\ARO-Clips\clip-001.mp4" --start 45 --duration 35 --permission permission.json --confirm-authorized --vertical
```

- `--start` is seconds from the beginning of that exact local file.
- `--duration` is clip length in seconds (maximum 600).
- `--vertical` creates a centered 9:16, 1080x1920 output. Remove it to keep the source aspect ratio.
- Choose a new output filename for every clip. Existing files are never overwritten.

## 5. Verify the project

```powershell
py -m compileall -q backend tests
py -m unittest discover -s tests -v
```

The permission file is an operator attestation, not legal verification. Game footage, music, and third-party material can have separate rights. Review the rendered clip before any distribution.
