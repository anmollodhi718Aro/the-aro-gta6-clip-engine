param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$launcher = Get-Command py -ErrorAction SilentlyContinue
$launcherArgs = @()

if ($launcher) {
    $pythonExe = $launcher.Source
    $launcherArgs = @("-3.11")
} else {
    $launcher = Get-Command python -ErrorAction SilentlyContinue
    if (-not $launcher) {
        throw "Python 3.11+ was not found. Install Python, then reopen PowerShell."
    }
    $pythonExe = $launcher.Source
}

Push-Location $repoRoot
try {
    & $pythonExe @launcherArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
    if ($LASTEXITCODE -ne 0) {
        throw "Python 3.11 or newer is required. If using the Python launcher, install Python 3.11+ and retry."
    }

    Write-Host "Starting THE ARO Studio at http://127.0.0.1:$Port"
    Write-Host "Keep this PowerShell window open. Press Ctrl+C to stop the dashboard."
    & $pythonExe @launcherArgs "THE_ARO_STUDIO.py" --host "127.0.0.1" --port $Port
    if ($LASTEXITCODE -ne 0) {
        throw "THE ARO Studio exited with code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
