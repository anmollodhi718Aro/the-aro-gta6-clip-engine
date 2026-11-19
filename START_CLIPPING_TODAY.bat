@echo off
setlocal
cd /d "%~dp0"
title THE ARO GTA 6 Clip Engine - Start Clipping Today

echo.
echo ================================================
echo   THE ARO GTA 6 CLIP ENGINE
echo   Preflight, tests, synthetic render, then wizard
echo ================================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\check_project.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" goto failed

echo.
echo [4/4] Verifying landscape and vertical FFmpeg rendering with synthetic footage...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\smoke_test_render.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" goto failed

echo.
echo All preflight checks passed. Starting the local clip wizard...
echo Use only footage you own or are explicitly authorized to edit and distribute.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\manual_clip_wizard.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" goto failed

echo.
echo Wizard finished. Review the session folder, MP4 files, and local review dashboard.
pause
exit /b 0

:failed
echo.
echo STARTUP STOPPED. Read the error above and fix the reported issue before rendering.
pause
exit /b %EXIT_CODE%
