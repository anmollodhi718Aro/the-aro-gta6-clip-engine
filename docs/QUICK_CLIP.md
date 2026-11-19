# Quick Clip: First Export

Use this when you already have a local gameplay recording and know the moment's
start and end times. It is the shortest path to your first edited clip without
waiting for chat analysis or automatic highlight detection.

## 1. Install FFmpeg

Install FFmpeg for your operating system and make sure `ffmpeg` is available
on your PATH. Python 3.11+ is required for the project.

## 2. Export one clip

Run this from the repository root:

```bash
python -m backend.app.quick_clip "recordings/gta_gameplay.mp4" \
  --start 42.5 \
  --end 68.0 \
  --output "clips/gta_moment_001.mp4" \
  --confirm-rights
```

Windows PowerShell users can run the same command on one line:\n\n```powershell\npy -3.11 -m backend.app.quick_clip "recordings\\gta_gameplay.mp4" --start 42.5 --end 68 --output "clips\\gta_moment_001.mp4" --confirm-rights\n```\n\nReplace the example paths and times with your own recording and selected moment.
Times are seconds from the beginning of that exact file. The command only accepts
local files, limits each clip to 180 seconds, and refuses to overwrite an output.
The explicit confirmation is for a recording you own or are authorized to edit.

## 3. Check the result

Open the exported MP4 and check the beginning/end, audio, and picture before using
it. This command creates a local edit only. It does not crop to vertical, add
captions, upload, or publish.

## 4. Continue to the full workflow

For chat-driven candidate discovery and batch exports, see
[Measured Clip Candidate Pack](CLIP_CANDIDATE_PACK.md) and
[Human-Approved Batch Rendering](BATCH_RENDERING.md). Automatic gameplay-scene
detection and automatic chat/video clock synchronization are not implemented.
