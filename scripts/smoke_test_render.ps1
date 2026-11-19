$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repoRoot

Write-Host "THE ARO | Synthetic render smoke test" -ForegroundColor Cyan
Write-Host "Creates a generated test pattern only. It does not use or publish GTA footage."

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
if (-not $pythonExe) { throw "Python 3.11+ not found." }
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw "FFmpeg is missing from PATH." }
if (-not (Get-Command ffprobe -ErrorAction SilentlyContinue)) { throw "ffprobe is missing from PATH." }

$stamp = (Get-Date -Format "yyyyMMdd_HHmmss") + "_" + [guid]::NewGuid().ToString("N").Substring(0,8)
$session = Join-Path $repoRoot ("smoke_test_output\" + $stamp)
New-Item -ItemType Directory -Path $session -Force | Out-Null
$media = Join-Path $session "synthetic_test_pattern.mp4"
$json = Join-Path $session "manual_clips.json"
$csv = Join-Path $session "manual_clips.csv"
$renderRoot = Join-Path $session "rendered"

Write-Host "[1/4] Generate a 12-second synthetic test video..." -ForegroundColor Yellow
& ffmpeg -nostdin -hide_banner -loglevel error -n -f lavfi -i "testsrc=size=640x360:rate=30" -t 12 -an -c:v libx264 -preset ultrafast -pix_fmt yuv420p $media
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $media)) { throw "Could not generate the synthetic test video." }

$payload = @{
    source_id = "synthetic-smoke-test-$stamp"
    clips = @(@{ start_seconds = 2.0; end_seconds = 8.0; note = "Synthetic pipeline verification only" })
} | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText($json, $payload + [Environment]::NewLine, ([System.Text.UTF8Encoding]::new($false)))

Write-Host "[2/4] Build manual clip plan..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m backend.app.manual_clip $json --output $csv
if ($LASTEXITCODE -ne 0) { throw "Manual clip plan generation failed." }

Write-Host "[3/4] Run dry-run..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m backend.app.batch_render $csv --media $media --approve 1 --output-dir $renderRoot
if ($LASTEXITCODE -ne 0) { throw "Dry-run failed." }

Write-Host "[4/4] Render and verify the generated test clip..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m backend.app.batch_render $csv --media $media --approve 1 --output-dir $renderRoot --execute --confirm-rights
if ($LASTEXITCODE -ne 0) { throw "Synthetic render failed." }

$runDir = Get-ChildItem -LiteralPath $renderRoot -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $runDir) { throw "Render run folder was not created." }
$report = Join-Path $runDir.FullName "batch_render_report.json"
if (-not (Test-Path -LiteralPath $report)) { throw "Render report was not created." }
$rows = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
$rendered = @($rows | Where-Object { $_.status -eq "rendered" })
if ($rendered.Count -ne 1) { throw "Expected exactly one rendered clip in the report." }
$output = $rendered[0].output_path
if (-not (Test-Path -LiteralPath $output)) { throw "Rendered MP4 is missing: $output" }

$probe = & ffprobe -v error -show_entries "format=duration:stream=codec_type" -of json $output
if ($LASTEXITCODE -ne 0) { throw "ffprobe could not inspect the rendered MP4." }
$metadata = $probe | ConvertFrom-Json
if (-not (@($metadata.streams | Where-Object { $_.codec_type -eq "video" }).Count -gt 0)) { throw "Rendered file has no video stream." }
$duration = [double]$metadata.format.duration
if ($duration -le 0 -or $duration -gt 7) { throw "Rendered clip duration is outside the expected 6-second smoke-test range." }

Write-Host ""
Write-Host "SMOKE TEST PASSED" -ForegroundColor Green
Write-Host "Synthetic MP4: $output"
Write-Host "Duration: $duration seconds"
Write-Host "Session logs: $session"
Write-Host "This verifies local tooling only. It does not verify GTA footage or content rights."
