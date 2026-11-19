@echo off
setlocal
cd /d "%~dp0"
title THE ARO GTA 6 Clip Engine - Start Clipping Today

echo ==========================================
echo       THE ARO GTA 6 CLIP ENGINE
echo          GUIDED FIRST CLIP
echo ==========================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\first_clip.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if not "%EXIT_CODE%"=="0" (
  echo Clipping stopped with an error. Read the message above.
) else (
  echo Wizard finished. Review the session folder and rendered MP4.
)
pause
exit /b %EXIT_CODE%
