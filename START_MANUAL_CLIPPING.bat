@echo off
setlocal
cd /d "%~dp0"
title THE ARO GTA 6 Manual Clipper

echo ==========================================
echo    THE ARO GTA 6 MANUAL CLIP WIZARD
echo ==========================================
echo.
where powershell >nul 2>nul
if errorlevel 1 (
  echo ERROR: Windows PowerShell was not found.
  pause
  exit /b 1
)
if not exist "scripts\manual_clip_wizard.ps1" (
  echo ERROR: scripts\manual_clip_wizard.ps1 is missing.
  echo Update the integration/release-candidate branch.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\manual_clip_wizard.ps1"
if errorlevel 1 (
  echo.
  echo The clip wizard stopped. Read the error above.
  pause
  exit /b 1
)
echo.
echo Wizard finished. Review your local session folder before sharing anything.
pause
endlocal
