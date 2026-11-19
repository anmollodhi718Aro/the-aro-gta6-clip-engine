@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_today.ps1"
if errorlevel 1 (
  echo.
  echo Startup stopped. Read the error above, then press any key.
  pause >nul
)
endlocal
