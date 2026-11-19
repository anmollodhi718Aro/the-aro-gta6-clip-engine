param()

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

# Prefer an explicit Python 3.11 launcher target. Do not silently select an
# older default Python just because the Windows py launcher exists.
$pythonExe = $null
$pythonArgs = @()
$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher) {
    & $launcher.Source -3.11 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" *> $null
    if ($LASTEXITCODE -eq 0) {
        $pythonExe = $launcher.Source
        $pythonArgs = @("-3.11")
    }
}
if (-not $pythonExe) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" *> $null
        if ($LASTEXITCODE -eq 0) { $pythonExe = $python.Source }
    }
}
if (-not $pythonExe) {
    throw "Python 3.11+ was not found. Install Python 3.11 or newer and reopen PowerShell."
}

Push-Location $repoRoot
try {
    & $pythonExe @pythonArgs -c "import sys; print('Using Python', sys.version.split()[0])"
    if ($LASTEXITCODE -ne 0) { throw "Python preflight failed." }

    foreach ($tool in @("ffmpeg", "ffprobe")) {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
            throw "$tool was not found on PATH. Install FFmpeg (including ffprobe), reopen PowerShell, and retry."
        }
    }

    Write-Host ""
    Write-Host "THE ARO - Guided First Clip" -ForegroundColor Cyan
    Write-Host "Local recording only. No stream downloads, uploads, or automatic publishing."
    $mediaInput = Read-Host "Full path to your own or authorized local video file"
    if ([string]::IsNullOrWhiteSpace($mediaInput)) { throw "A video path is required." }
    $media = (Resolve-Path -LiteralPath $mediaInput).Path
    if (-not (Test-Path -LiteralPath $media -PathType Leaf)) { throw "The selected media path is not a file." }

    # Validate the real video stream and duration before accepting timestamps.
    $videoStream = (& ffprobe -v error -select_streams v:0 -show_entries stream=codec_type -of csv=p=0 $media | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $videoStream -ne "video") {
        throw "ffprobe could not find a readable video stream in the selected file."
    }
    $durationText = (& ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $media | Out-String).Trim()
    $mediaDuration = 0.0
    $durationOk = [double]::TryParse(
        $durationText,
        [Globalization.NumberStyles]::Float,
        [Globalization.CultureInfo]::InvariantCulture,
        [ref]$mediaDuration
    )
    if ($LASTEXITCODE -ne 0 -or -not $durationOk -or [double]::IsNaN($mediaDuration) -or
        [double]::IsInfinity($mediaDuration) -or $mediaDuration -le 0) {
        throw "Could not read a finite, positive duration from the selected video."
    }
    Write-Host ("Verified video duration: {0:N2} seconds" -f $mediaDuration) -ForegroundColor Gray

    $sourceId = Read-Host "Short source ID (Enter to use the video filename)"
    if ([string]::IsNullOrWhiteSpace($sourceId)) { $sourceId = [IO.Path]::GetFileNameWithoutExtension($media) }

    function Read-Seconds([string]$Prompt) {
        while ($true) {
            $raw = Read-Host $Prompt
            $value = 0.0
            $ok = [double]::TryParse(
                $raw,
                [Globalization.NumberStyles]::Float,
                [Globalization.CultureInfo]::InvariantCulture,
                [ref]$value
            )
            if ($ok -and -not [double]::IsNaN($value) -and -not [double]::IsInfinity($value) -and $value -ge 0) {
                return $value
            }
            Write-Host "Enter a number of seconds, for example 42 or 42.5." -ForegroundColor Yellow
        }
    }

    $start = Read-Seconds "Clip start in seconds from the beginning of the video"
    $end = Read-Seconds "Clip end in seconds (maximum clip length: 180 seconds)"
    if ($end -le $start) { throw "End time must be greater than start time." }
    if (($end - $start) -gt 180) { throw "This project limits each clip to 180 seconds. Choose a shorter range." }
    if ($end -gt $mediaDuration) {
        throw ("Clip end ({0:N3}s) exceeds the verified video duration ({1:N3}s)." -f $end, $mediaDuration)
    }

    # Timestamp plus random suffix prevents simultaneous sessions from colliding.
    $stamp = (Get-Date -Format "yyyyMMdd-HHmmss-fff") + "-" + ([guid]::NewGuid().ToString("N").Substring(0,8))
    $sessionDir = Join-Path $repoRoot "aro_studio_data\manual_sessions"
    $renderRoot = Join-Path $repoRoot "rendered_clips"
    New-Item -ItemType Directory -Force -Path $sessionDir | Out-Null
    New-Item -ItemType Directory -Force -Path $renderRoot | Out-Null

    $sessionJson = Join-Path $sessionDir "session-$stamp.json"
    $candidateCsv = Join-Path $sessionDir "candidates-$stamp.csv"
    $dryReport = Join-Path $sessionDir "dry-run-$stamp.json"
    $renderReport = Join-Path $sessionDir "render-$stamp.json"
    $reviewHtml = Join-Path $sessionDir "review-$stamp.html"

    $payload = @{
        source_id = $sourceId
        clips = @(@{
            start_seconds = $start
            end_seconds = $end
            note = "Manually selected by the owner; inspect before distribution."
        })
    } | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($sessionJson, $payload, [System.Text.UTF8Encoding]::new($false))

    Write-Host ""
    Write-Host "[1/3] Preparing the candidate CSV..." -ForegroundColor Yellow
    & $pythonExe @pythonArgs -m backend.app.manual_clip $sessionJson --output $candidateCsv
    if ($LASTEXITCODE -ne 0) { throw "Manual clip preparation failed." }

    Write-Host ""
    Write-Host "[2/3] Running a no-render dry run..." -ForegroundColor Yellow
    & $pythonExe @pythonArgs -m backend.app.batch_render $candidateCsv --media $media --approve 1 --output-dir $renderRoot --report $dryReport
    if ($LASTEXITCODE -ne 0) { throw "Dry-run failed. No clip was rendered." }
    Write-Host "Dry-run report: $dryReport" -ForegroundColor Green

    $renderChoice = Read-Host "After reviewing the dry-run, type RENDER to continue (anything else exits)"
    if ($renderChoice -cne "RENDER") {
        Write-Host "Stopped safely. No video was rendered. Your session files are in $sessionDir"
        return
    }

    Write-Host "Only continue if you own or have explicit permission to edit and distribute this exact recording, and have checked any third-party content rights." -ForegroundColor Yellow
    $rightsChoice = Read-Host "Type I CONFIRM RIGHTS to authorize this local render"
    if ($rightsChoice -cne "I CONFIRM RIGHTS") {
        Write-Host "Stopped safely. No video was rendered."
        return
    }

    Write-Host ""
    Write-Host "[3/3] Rendering the approved local clip..." -ForegroundColor Yellow
    & $pythonExe @pythonArgs -m backend.app.batch_render $candidateCsv --media $media --approve 1 --output-dir $renderRoot --report $renderReport --execute --confirm-rights
    if ($LASTEXITCODE -ne 0) { throw "Rendering failed. Inspect the report and local output folder: $renderRoot" }

    & $pythonExe @pythonArgs -m backend.app.review_dashboard $renderReport --output $reviewHtml
    if ($LASTEXITCODE -ne 0) { throw "Clip rendered, but review-page generation failed. Report: $renderReport" }

    Write-Host ""
    Write-Host "Clip workflow completed. Review the MP4 before sharing." -ForegroundColor Green
    Write-Host "Render report: $renderReport"
    Write-Host "Review page:   $reviewHtml"
    Start-Process -FilePath $reviewHtml
}
finally {
    Pop-Location
}
