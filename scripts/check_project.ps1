$ErrorActionPreference = "Stop"

Write-Host "THE ARO GTA 6 Clip Engine - local checks" -ForegroundColor Cyan

python --version
if ($LASTEXITCODE -ne 0) { throw "Python was not found on PATH." }

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 or newer is required." }

Write-Host "`n[1/3] Compile Python source..." -ForegroundColor Yellow
python -m compileall -q backend tests THE_ARO_STUDIO.py
if ($LASTEXITCODE -ne 0) { throw "Compile check failed." }

Write-Host "`n[2/3] Run unit tests..." -ForegroundColor Yellow
python -m unittest discover -s tests -v
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
