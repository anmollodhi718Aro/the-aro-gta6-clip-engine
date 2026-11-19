#!/usr/bin/env bash
set -euo pipefail

echo "THE ARO GTA 6 Clip Engine - local render preflight"

python_bin="$(command -v python3 || true)"
if [[ -z "$python_bin" ]]; then
  echo "ERROR: Python 3 was not found. Install Python 3.11+ and ensure python3 is on PATH." >&2
  exit 1
fi
"$python_bin" --version
"$python_bin" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("ERROR: Python 3.11 or newer is required.")
PY

# Rendering is a core product capability, not an optional extra. A successful
# preflight must never imply the machine can clip when either media tool is absent.
ffmpeg_bin="$(command -v ffmpeg || true)"
if [[ -z "$ffmpeg_bin" ]]; then
  echo "ERROR: FFmpeg was not found on PATH. Install FFmpeg, reopen the terminal, and retry." >&2
  exit 1
fi
ffprobe_bin="$(command -v ffprobe || true)"
if [[ -z "$ffprobe_bin" ]]; then
  echo "ERROR: ffprobe was not found on PATH. Install the FFmpeg package that includes ffprobe, reopen the terminal, and retry." >&2
  exit 1
fi

echo
echo "FFmpeg: $ffmpeg_bin"
"$ffmpeg_bin" -version | sed -n '1p'
echo "FFprobe: $ffprobe_bin"
"$ffprobe_bin" -version | sed -n '1p'

echo
echo "[1/2] Compile Python source..."
"$python_bin" -m compileall -q backend tests THE_ARO_STUDIO.py

echo
echo "[2/2] Run unit tests..."
"$python_bin" -m unittest discover -s tests -v

echo
echo "Preflight passed: Python, FFmpeg, ffprobe, compilation, and unit tests are available."
