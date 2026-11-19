$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repoRoot
try {
    Write-Host "THE ARO | Synthetic render smoke test" -ForegroundColor Cyan
    Write-Host "Uses generated test footage only. No GTA footage is downloaded or published."

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
    if (-not $pythonExe) { throw "Python 3.11+ not found. Install Python 3.11 or newer." }
    foreach ($tool in @("ffmpeg", "ffprobe")) {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
            throw "$tool is missing from PATH."
        }
    }

    # Fail early with a useful message instead of an opaque encoder error.
    $encoderList = (& ffmpeg -hide_banner -encoders 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0 -or $encoderList -notmatch "(?m)\blibx264\b") {
        throw "FFmpeg is available, but the libx264 H.264 encoder is missing. Install an FFmpeg build that includes libx264, then rerun this check."
    }

    $stamp = (Get-Date -Format "yyyyMMdd_HHmmss") + "_" + [guid]::NewGuid().ToString("N").Substring(0, 8)
    $session = Join-Path $repoRoot ("smoke_test_output\" + $stamp)
    New-Item -ItemType Directory -Path $session -Force | Out-Null
    $media = Join-Path $session "synthetic_test_pattern.mp4"
    $json = Join-Path $session "manual_clips.json"
    $csv = Join-Path $session "manual_clips.csv"

    Write-Host "[1/5] Generate a 12-second synthetic video..." -ForegroundColor Yellow
    & ffmpeg -nostdin -hide_banner -loglevel error -n -f lavfi -i "testsrc=size=640x360:rate=30" -t 12 -an -c:v libx264 -preset ultrafast -pix_fmt yuv420p $media
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $media -PathType Leaf)) {
        throw "Could not generate the synthetic test video."
    }

    $payload = @{
        source_id = "synthetic-smoke-test-$stamp"
        clips = @(@{ start_seconds = 2.0; end_seconds = 8.0; note = "Synthetic pipeline verification only" })
    } | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($json, $payload + [Environment]::NewLine, ([System.Text.UTF8Encoding]::new($false)))

    Write-Host "[2/5] Build the manual clip plan..." -ForegroundColor Yellow
    & $pythonExe @pythonPrefix -m backend.app.manual_clip $json --output $csv
    if ($LASTEXITCODE -ne 0) { throw "Manual clip plan generation failed." }

    foreach ($mode in @("landscape", "vertical")) {
        $renderRoot = Join-Path $session $mode
        $modeArgs = @()
        if ($mode -eq "vertical") { $modeArgs = @("--vertical") }

        Write-Host "[3/5] $mode dry-run..." -ForegroundColor Yellow
        & $pythonExe @pythonPrefix -m backend.app.batch_render $csv --media $media --approve 1 --output-dir $renderRoot @modeArgs
        if ($LASTEXITCODE -ne 0) { throw "$mode dry-run failed." }

        Write-Host "[4/5] Render and verify $mode output..." -ForegroundColor Yellow
        & $pythonExe @pythonPrefix -m backend.app.batch_render $csv --media $media --approve 1 --output-dir $renderRoot @modeArgs --execute --confirm-rights
        if ($LASTEXITCODE -ne 0) { throw "$mode synthetic render failed." }

        $runDir = Get-ChildItem -LiteralPath $renderRoot -Directory |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if (-not $runDir) { throw "$mode render run folder was not created." }
        $report = Join-Path $runDir.FullName "batch_render_report.json"
        if (-not (Test-Path -LiteralPath $report -PathType Leaf)) { throw "$mode render report was not created." }

        $rows = @(Get-Content -LiteralPath $report -Raw | ConvertFrom-Json)
        $rendered = @($rows | Where-Object { $_.status -eq "rendered" })
        if ($rendered.Count -ne 1) { throw "Expected exactly one rendered $mode clip in the report." }
        $output = $rendered[0].output_path
        if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw "Rendered MP4 is missing: $output" }
        $outputItem = Get-Item -LiteralPath $output
        if ($outputItem.Length -le 0) { throw "Rendered MP4 is empty: $output" }

        $probeText = & ffprobe -v error -show_entries "format=duration:stream=codec_type,width,height" -of json $output
        if ($LASTEXITCODE -ne 0) { throw "ffprobe could not inspect the $mode MP4." }
        $metadata = $probeText | ConvertFrom-Json
        $video = @($metadata.streams | Where-Object { $_.codec_type -eq "video" })
        if ($video.Count -lt 1) { throw "$mode output has no video stream." }
        $duration = 0.0
        $durationText = [string]$metadata.format.duration
        if (-not [double]::TryParse($durationText, [System.Globalization.NumberStyles]::Float,
            [System.Globalization.CultureInfo]::InvariantCulture, [ref]$duration) -or
            [double]::IsNaN($duration) -or [double]::IsInfinity($duration) -or
            $duration -le 0 -or $duration -gt 7) {
            throw "$mode duration is not finite and positive or is outside the expected six-second range."
        }

        if ($mode -eq "vertical" -and ($video[0].width -ne 1080 -or $video[0].height -ne 1920)) {
            throw "Vertical output must be 1080x1920; got $($video[0].width)x$($video[0].height)."
        }
        if ($mode -eq "landscape" -and ($video[0].width -ne 640 -or $video[0].height -ne 360)) {
            throw "Landscape output must preserve 640x360; got $($video[0].width)x$($video[0].height)."
        }
        Write-Host ("Verified {0}: {1}x{2}, {3:N2}s" -f $mode, $video[0].width, $video[0].height, $duration) -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "SMOKE TEST PASSED: landscape and vertical render paths verified." -ForegroundColor Green
    Write-Host "Synthetic test artifacts: $session"
    Write-Host "This verifies local tooling only, not GTA footage or third-party content rights."
}
finally {
    Pop-Location
}
