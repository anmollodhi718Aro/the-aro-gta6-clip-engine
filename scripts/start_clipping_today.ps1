param()

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repoRoot

Write-Host ""
Write-Host "THE ARO GTA 6 Clip Engine - Start Clipping Today" -ForegroundColor Cyan
Write-Host "Preflight checks run before the manual clip wizard."
Write-Host ""

$pythonExe = $null
$pythonPrefix = @()
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    & $py.Source -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" *> $null
    if ($LASTEXITCODE -eq 0) {
        $pythonExe = $py.Source
        $pythonPrefix = @("-3")
    }
}

if (-not $pythonExe) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" *> $null
        if ($LASTEXITCODE -eq 0) {
            $pythonExe = $python.Source
            $pythonPrefix = @()
        }
    }
}

if (-not $pythonExe) {
    throw "Python 3.11+ was not found. Install Python 3.11 or newer, then reopen this window."
}

$pythonVersion = & $pythonExe @pythonPrefix -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
if ($LASTEXITCODE -ne 0) { throw "Could not read the selected Python version." }
Write-Host "Python $pythonVersion found." -ForegroundColor Green

foreach ($toolName in @("ffmpeg", "ffprobe")) {
    if (-not (Get-Command $toolName -ErrorAction SilentlyContinue)) {
        throw "$toolName was not found on PATH. Install FFmpeg (including ffprobe), reopen this window, and retry."
    }
}
Write-Host "FFmpeg and ffprobe found." -ForegroundColor Green

Write-Host ""
Write-Host "[1/2] Compiling project source..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m compileall -q backend tests THE_ARO_STUDIO.py
if ($LASTEXITCODE -ne 0) { throw "Python compile check failed. No clip was rendered." }

Write-Host ""
Write-Host "[2/2] Running the complete test suite..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Unit tests failed. No clip was rendered. Review the failing test output." }

Write-Host ""
Write-Host "Preflight passed. Opening the manual clip wizard..." -ForegroundColor Green
& (Join-Path $PSScriptRoot "manual_clip_wizard.ps1")
if ($LASTEXITCODE -ne 0) { throw "The manual clip wizard reported an error." }
