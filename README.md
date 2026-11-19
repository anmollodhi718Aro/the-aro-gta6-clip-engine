# THE ARO GTA 6 Clip Engine

A local-first, zero-mandatory-dependency creator workflow for analysing authorized GTA 6 livestream chat, reviewing clip candidates, rendering from locally supplied authorized media, and producing original THE ARO commentary packs.

> This is the separate GTA 6 project, not the ARO History Engine or THE ARO Deployment Network.

## Start clipping today

**Fastest Windows route:** install Python 3.11+ and FFmpeg (including ffprobe), then double-click `START_CLIPPING_TODAY.bat`. It guides you through selecting up to 50 moments from a local recording, runs a dry-run, requires two explicit confirmations before rendering, and opens a local review dashboard. See [Manual Clipping](docs/MANUAL_CLIPPING.md).

For the full chat-assisted workflow and measured timestamp synchronization, see [First Clip Today](docs/FIRST_CLIP_TODAY.md).

## Requirements

- Python 3.11+
- FFmpeg and ffprobe on PATH for actual local video rendering and media preflight.
- No mandatory third-party Python packages.
- Optional YouTube stream/gRPC adapter dependencies: `pip install -e ".[youtube-stream]"`.
- A YouTube Data API key is required only for supported public live-chat API operations. Keep credentials in local environment configuration; never commit them.

## Start the unified local dashboard

```bash
python THE_ARO_STUDIO.py
```

Open `http://127.0.0.1:8765`. The dashboard is intentionally loopback-only.

See [Manual Clipping](docs/MANUAL_CLIPPING.md) for the fastest local-recording workflow and [First Clip Today](docs/FIRST_CLIP_TODAY.md) for the broader chat-assisted path.
