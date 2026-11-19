@echo off
setlocal
cd /d "%~dp0"
title THE ARO GTA 6 Clip Engine - Start Clipping Today
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\manual_clip_wizard.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if not "%EXIT_CODE%"=="0" (
  echo Clipping stopped with an error. Read the message above.
) else (
  echo Wizard finished. Review the session folder and rendered MP4.
)
pause
exit /b %EXIT_CODE%
