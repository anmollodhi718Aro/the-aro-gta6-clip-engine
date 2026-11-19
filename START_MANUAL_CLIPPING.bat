@echo off
setlocal
cd /d "%~dp0"
title THE ARO GTA 6 - Start Clipping Today
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\start_clipping_today.ps1"
if errorlevel 1 (
  echo.
  echo Start Clipping Today stopped. No clip was rendered after a failed preflight.
  pause
)
endlocal
