$ErrorActionPreference = "Stop"

Write-Host "THE ARO GTA 6 Clip Engine - local checks" -ForegroundColor Cyan

# Select a supported runtime explicitly; do not accidentally use an older
# system Python when Python 3.11+ is installed side-by-side.
$pythonExe = $null
$pythonPrefix = @()
$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher) {
    & $launcher.Source -3.11 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" *> $null
    if ($LASTEXITCODE -eq 0) {
        $pythonExe = $launcher.Source
        $pythonPrefix = @("-3.11")
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
    throw "Python 3.11+ not found. Install Python 3.11 or newer and enable the Python launcher or Add to PATH."
}

& $pythonExe @pythonPrefix --version
if ($LASTEXITCODE -ne 0) { throw "Could not start the selected Python runtime." }

Write-Host "`n[1/3] Compile Python source..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m compileall -q backend tests THE_ARO_STUDIO.py
if ($LASTEXITCODE -ne 0) { throw "Compile check failed." }

Write-Host "`n[2/3] Run unit tests..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Unit tests failed. Review the failing test output above." }

Write-Host "`n[3/3] Check optional FFmpeg tools..." -ForegroundColor Yellow
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    ffmpeg -version | Select-Object -First 1
} else {
    Write-Warning "FFmpeg not found. Local MP4 rendering is unavailable."
}
if (Get-Command ffprobe -ErrorAction SilentlyContinue) {
    ffprobe -version | Select-Object -First 1
} else {
    Write-Warning "ffprobe not found. Actual-media duration validation will stop before rendering."
}

Write-Host "`nAll available local checks passed." -ForegroundColor Green
