$ErrorActionPreference = "Stop"

Write-Host "THE ARO GTA 6 Clip Engine - local checks" -ForegroundColor Cyan

$pythonExe = $null
$pythonPrefix = @()
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
        if ($LASTEXITCODE -eq 0) { $pythonExe = $python.Source }
    }
}
if (-not $pythonExe) { throw "Python 3.11+ not found. Install Python 3.11 or newer and enable the py launcher or add Python to PATH." }

& $pythonExe @pythonPrefix --version
if ($LASTEXITCODE -ne 0) { throw "Could not start the selected Python runtime." }

Write-Host "`n[1/3] Compile Python source..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m compileall -q backend tests THE_ARO_STUDIO.py
if ($LASTEXITCODE -ne 0) { throw "Compile check failed." }

Write-Host "`n[2/3] Run unit tests..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Unit tests failed. Review the failing test output above." }

Write-Host "`n[3/3] Verify required FFmpeg tools..." -ForegroundColor Yellow
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg) { throw "FFmpeg not found on PATH. Install FFmpeg with the libx264 encoder and reopen this window." }
$ffprobe = Get-Command ffprobe -ErrorAction SilentlyContinue
if (-not $ffprobe) { throw "ffprobe not found on PATH. Install FFmpeg including ffprobe and reopen this window." }

$ffmpegVersion = & $ffmpeg.Source -version 2>&1 | Select-Object -First 1
if ($LASTEXITCODE -ne 0) { throw "FFmpeg could not start." }
Write-Host $ffmpegVersion

$encoderList = & $ffmpeg.Source -hide_banner -encoders 2>&1 | Out-String
if ($LASTEXITCODE -ne 0 -or $encoderList -notmatch "(?m)\blibx264\b") {
    throw "FFmpeg is installed but the required libx264 encoder is unavailable."
}
$ffprobeVersion = & $ffprobe.Source -version 2>&1 | Select-Object -First 1
if ($LASTEXITCODE -ne 0) { throw "ffprobe could not start." }
Write-Host $ffprobeVersion

Write-Host "`nPython checks and required media-tool preflight passed." -ForegroundColor Green
