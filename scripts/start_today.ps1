$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

Write-Host ""
Write-Host "THE ARO GTA 6 Clip Engine - First Run" -ForegroundColor Cyan
Write-Host "This launcher runs local checks, then opens the localhost Studio." -ForegroundColor Gray

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    $pythonCommand = $py.Source
    $pythonPrefix = @("-3")
} else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { throw "Python 3.11+ not found. Install Python and enable Add to PATH." }
    $pythonCommand = $python.Source
    $pythonPrefix = @()
}

& $pythonCommand @pythonPrefix --version
if ($LASTEXITCODE -ne 0) { throw "Python could not start." }
& $pythonCommand @pythonPrefix -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 or newer is required." }

Write-Host "[1/2] Compiling project..." -ForegroundColor Yellow
& $pythonCommand @pythonPrefix -m compileall -q backend tests THE_ARO_STUDIO.py
if ($LASTEXITCODE -ne 0) { throw "Compile check failed. Fix the reported Python errors first." }

Write-Host "[2/2] Running test suite..." -ForegroundColor Yellow
& $pythonCommand @pythonPrefix -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Tests failed. Studio was not started; review the test output above." }

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Warning "FFmpeg is missing. Studio can open, but MP4 rendering will not work until FFmpeg is installed and on PATH."
}
if (-not (Get-Command ffprobe -ErrorAction SilentlyContinue)) {
    Write-Warning "ffprobe is missing. Actual-media preflight will block rendering until ffprobe is installed and on PATH."
}

$port = 8765
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
try {
    $listener.Start()
    $listener.Stop()
} catch {
    try { $listener.Stop() } catch {}
    throw "Port $port is already in use. Close the existing Studio or change its port before starting another copy."
}

Write-Host "Starting local Studio..." -ForegroundColor Green
$arguments = @()
$arguments += $pythonPrefix
$arguments += "THE_ARO_STUDIO.py"
Start-Process -FilePath $pythonCommand -ArgumentList $arguments -WorkingDirectory $PSScriptRoot
Start-Sleep -Seconds 2

try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port" -TimeoutSec 3 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Start-Process "http://127.0.0.1:$port"
        Write-Host "Studio is ready: http://127.0.0.1:$port" -ForegroundColor Green
    } else {
        Write-Warning "Studio process started. Open http://127.0.0.1:$port manually."
    }
} catch {
    Write-Warning "Studio process was launched. If the browser did not open, visit http://127.0.0.1:$port manually."
}
Write-Host "Keep the Studio terminal window open. Press Ctrl+C there to stop it." -ForegroundColor Gray
