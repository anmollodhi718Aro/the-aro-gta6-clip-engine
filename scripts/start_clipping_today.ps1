$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repoRoot
$port = 8765
$url = "http://127.0.0.1:$port"
$dataDir = Join-Path $repoRoot "aro_studio_data"
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
$stdoutLog = Join-Path $dataDir "studio.stdout.log"
$stderrLog = Join-Path $dataDir "studio.stderr.log"

Write-Host ""
Write-Host "THE ARO GTA 6 Clip Engine - Start Clipping Today" -ForegroundColor Cyan
Write-Host "Local-only workflow. No video download, upload, or auto-publishing." -ForegroundColor Gray
Write-Host ""

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    $pythonExe = $py.Source
    $pythonPrefix = @("-3")
} else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { throw "Python 3.11+ was not found. Install Python and enable Add to PATH." }
    $pythonExe = $python.Source
    $pythonPrefix = @()
}

& $pythonExe @pythonPrefix --version
if ($LASTEXITCODE -ne 0) { throw "Python could not start." }
& $pythonExe @pythonPrefix -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 or newer is required." }

Write-Host "[1/2] Compiling project..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m compileall -q backend tests THE_ARO_STUDIO.py
if ($LASTEXITCODE -ne 0) { throw "Compile check failed. Studio was not started." }

Write-Host "[2/2] Running the full test suite..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Tests failed. Studio was not started. Fix the failures shown above." }

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Warning "FFmpeg is missing. The dashboard can open, but MP4 rendering will not work."
}
if (-not (Get-Command ffprobe -ErrorAction SilentlyContinue)) {
    Write-Warning "ffprobe is missing. Actual-media preflight will block rendering."
}

$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
try {
    $listener.Start()
    $listener.Stop()
} catch {
    try { $listener.Stop() } catch {}
    throw "Port $port is already in use. Close the existing Studio before starting another copy."
}

$arguments = @()
$arguments += $pythonPrefix
$arguments += @("THE_ARO_STUDIO.py", "--host", "127.0.0.1", "--port", "$port")
$argumentLine = $arguments -join " "

Write-Host "Starting THE ARO Studio..." -ForegroundColor Green
$process = Start-Process -FilePath $pythonExe -ArgumentList $argumentLine -WorkingDirectory $repoRoot -PassThru -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog

$ready = $false
for ($attempt = 0; $attempt -lt 15; $attempt++) {
    if ($process.HasExited) { throw "Studio exited during startup. Check $stderrLog" }
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 2 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        # The local server may need another moment to bind its loopback port.
    }
    Start-Sleep -Seconds 1
}

if (-not $ready) {
    if (-not $process.HasExited) { Stop-Process -Id $process.Id -ErrorAction SilentlyContinue }
    throw "Studio did not become ready within 15 seconds. Check $stderrLog"
}

Start-Process $url
Write-Host ""
Write-Host "THE ARO Studio is ready: $url" -ForegroundColor Green
Write-Host "Server logs: $dataDir" -ForegroundColor Gray
Write-Host "Next: use Manual Clipping to select moments from your own authorized local recording." -ForegroundColor Gray
Write-Host "Rendering requires FFmpeg, ffprobe, human approval, and rights confirmation." -ForegroundColor Gray
