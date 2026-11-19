@echo off
setlocal
cd /d "%~dp0"
title THE ARO GTA 6 Clip Engine

echo ==========================================
echo       THE ARO GTA 6 CLIP ENGINE
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python was not found.
  echo Install Python 3.11 or newer and enable "Add Python to PATH".
  pause
  exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 (
  echo ERROR: Python 3.11 or newer is required.
  python --version
  pause
  exit /b 1
)

echo Python:
python --version
echo.

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo WARNING: FFmpeg is not on PATH. Dashboard can open, but MP4 rendering is unavailable.
) else (
  echo FFmpeg detected.
)
where ffprobe >nul 2>nul
if errorlevel 1 (
  echo WARNING: ffprobe is not on PATH. Real-media preflight will block rendering.
) else (
  echo ffprobe detected.
)

echo.
echo Starting THE ARO Studio at http://127.0.0.1:8765
echo Keep this window open while using the dashboard.
echo Press Ctrl+C here to stop the local server.
echo.
python THE_ARO_STUDIO.py
if errorlevel 1 (
  echo.
  echo THE ARO Studio stopped with an error. Read the message above.
  pause
)
endlocal
