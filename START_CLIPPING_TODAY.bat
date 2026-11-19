@echo off
setlocal
cd /d "%~dp0"
title THE ARO GTA 6 Clip Engine - Start Clipping Today

echo.
echo [1/2] Checking Python, FFmpeg, FFprobe, source compilation and tests...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\check_project.ps1"
if errorlevel 1 goto preflight_failed

echo.
echo [2/2] Starting the local manual clip wizard...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\manual_clip_wizard.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if not "%EXIT_CODE%"=="0" (
  echo Clipping stopped with an error. Read the message above.
) else (
  echo Wizard finished. Review the session folder, MP4 files, and local review dashboard.
)
pause
exit /b %EXIT_CODE%

:preflight_failed
echo.
echo Preflight failed. The clip wizard was not started and no video was rendered.
pause
exit /b 1
