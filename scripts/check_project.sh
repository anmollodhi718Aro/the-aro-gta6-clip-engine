#!/usr/bin/env bash
set -euo pipefail

echo "THE ARO GTA 6 Clip Engine - local checks"
python3 --version
python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required.")
PY

echo
echo "[1/3] Compile Python source..."
python3 -m compileall -q backend tests THE_ARO_STUDIO.py

echo
echo "[2/3] Run unit tests..."
python3 -m unittest discover -s tests -v

echo
echo "[3/3] Check optional FFmpeg..."
if command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -version | head -n 1
else
  echo "FFmpeg not found. Python tests completed, but local MP4 rendering needs FFmpeg."
fi

echo
echo "All available local checks passed."
