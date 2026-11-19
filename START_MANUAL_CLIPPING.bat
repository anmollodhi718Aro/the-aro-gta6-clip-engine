@echo off
setlocal
cd /d "%~dp0"
title THE ARO Manual Clip Wizard
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\manual_clip_wizard.ps1"
if errorlevel 1 (
  echo.
  echo The clip wizard stopped with an error. Read the message above.
  pause
)
endlocal
