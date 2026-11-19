@echo off
setlocal
cd /d "%~dp0"
title THE ARO GTA 6 Clip Engine - Start Clipping Today
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\manual_clip_wizard.ps1"
if errorlevel 1 (
  echo.
  echo Clipping stopped with an error. Read the message above.
  pause
)
endlocal
