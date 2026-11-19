$ErrorActionPreference = "Stop"

Write-Host "THE ARO GTA 6 Clip Engine - first-clip preflight" -ForegroundColor Cyan

$pythonExe = $null
$pythonPrefix = @()

# Select a supported Python 3 runtime consistently with the clip wizard.
$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher) {
    & $launcher.Source -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" *> $null
    if ($LASTEXITCODE -eq 0) {
        $pythonExe = $launcher.Source
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
    throw "Python 3.11+ was not found. Install Python 3.11 or newer and enable the Python launcher or Add to PATH."
}

Write-Host "`nPython runtime:" -ForegroundColor Yellow
& $pythonExe @pythonPrefix --version
if ($LASTEXITCODE -ne 0) { throw "Could not start the selected Python runtime." }

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg) { throw "FFmpeg is required for clipping but was not found on PATH. Install FFmpeg and reopen this window." }
$ffprobe = Get-Command ffprobe -ErrorAction SilentlyContinue
if (-not $ffprobe) { throw "ffprobe is required for media validation but was not found on PATH. Install FFmpeg including ffprobe and reopen this window." }

Write-Host "`nFFmpeg:" -ForegroundColor Yellow
& $ffmpeg.Source -version | Select-Object -First 1
if ($LASTEXITCODE -ne 0) { throw "FFmpeg could not be executed." }

Write-Host "`nFFprobe:" -ForegroundColor Yellow
& $ffprobe.Source -version | Select-Object -First 1
if ($LASTEXITCODE -ne 0) { throw "FFprobe could not be executed." }

Write-Host "`n[1/2] Compile Python source..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m compileall -q backend tests THE_ARO_STUDIO.py
if ($LASTEXITCODE -ne 0) { throw "Compile check failed." }

Write-Host "`n[2/2] Run the complete unit-test suite..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Unit tests failed. Clipping is blocked until the failures are fixed." }

Write-Host "`nPreflight passed. The manual clip wizard can now start." -ForegroundColor Green
