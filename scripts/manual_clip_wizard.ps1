param()

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repoRoot

function Read-ClipSeconds([string]$Prompt) {
    while ($true) {
        $raw = Read-Host $Prompt
        $value = 0.0
        $ok = [double]::TryParse(
            $raw,
            [System.Globalization.NumberStyles]::Float,
            [System.Globalization.CultureInfo]::InvariantCulture,
            [ref]$value
        )
        if ($ok -and -not [double]::IsNaN($value) -and -not [double]::IsInfinity($value)) {
            return $value
        }
        Write-Host "Enter a valid number of seconds (example: 125.5)." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "THE ARO GTA 6 Clip Engine - Manual Clip Wizard" -ForegroundColor Cyan
Write-Host "Use only a local recording you own or are authorized to edit and publish."
Write-Host ""

$pythonExe = $null
$pythonPrefix = @()

# Prefer the Windows Python launcher when it has a 3.11 runtime. If it does
# not, fall back to the active "python" on PATH instead of stopping early.
$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher) {
    & $launcher.Source -3.11 -c "import sys; print(sys.executable)" *> $null
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

& $pythonExe @pythonPrefix -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 or newer is required." }

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    throw "FFmpeg was not found on PATH. Install FFmpeg, reopen this window, and retry."
}
if (-not (Get-Command ffprobe -ErrorAction SilentlyContinue)) {
    throw "ffprobe was not found on PATH. Install FFmpeg (including ffprobe), reopen this window, and retry."
}

$mediaInput = Read-Host "Full path to your authorized local video file"
if ([string]::IsNullOrWhiteSpace($mediaInput)) { throw "No video path supplied." }
$mediaPath = (Resolve-Path -LiteralPath $mediaInput).Path
if (-not (Test-Path -LiteralPath $mediaPath -PathType Leaf)) { throw "The selected media path is not a file." }

$videoStream = & ffprobe -v error -select_streams v:0 -show_entries stream=codec_type -of csv=p=0 $mediaPath
if ($LASTEXITCODE -ne 0 -or [string]$videoStream -ne "video") {
    throw "The selected file does not contain a readable video stream."
}

$durationText = & ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $mediaPath
if ($LASTEXITCODE -ne 0) { throw "ffprobe could not read the selected video duration." }
$mediaDuration = 0.0
if (-not [double]::TryParse([string]$durationText, [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$mediaDuration) -or [double]::IsNaN($mediaDuration) -or [double]::IsInfinity($mediaDuration) -or $mediaDuration -le 0) {
    throw "Could not read a finite, positive video duration."
}
Write-Host ("Video duration: {0:N2} seconds" -f $mediaDuration) -ForegroundColor Gray

$start = Read-ClipSeconds "Clip start time in seconds"
$end = Read-ClipSeconds "Clip end time in seconds"
if ($start -lt 0 -or $end -le $start) { throw "Clip range must satisfy 0 <= start < end." }
if (($end - $start) -gt 180) { throw "Each clip must be 180 seconds or shorter." }
if ($end -gt $mediaDuration) { throw "Clip end is beyond the actual video duration." }

$note = Read-Host "Short note for this moment (optional)"
if ([string]::IsNullOrWhiteSpace($note)) { $note = "Manually selected moment; review before publishing." }

$stamp = (Get-Date -Format "yyyyMMdd_HHmmss") + "_" + ([guid]::NewGuid().ToString("N").Substring(0, 8))
$sessionDir = Join-Path $repoRoot ("manual_clip_sessions\" + $stamp)
New-Item -ItemType Directory -Path $sessionDir -ErrorAction Stop | Out-Null
$jsonPath = Join-Path $sessionDir "manual_clips.json"
$csvPath = Join-Path $sessionDir "manual_clips.csv"
$reportRoot = Join-Path $sessionDir "rendered"
$payload = @{
    source_id = [System.IO.Path]::GetFileName($mediaPath)
    clips = @(@{
        start_seconds = $start
        end_seconds = $end
        note = $note
    })
} | ConvertTo-Json -Depth 5
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($jsonPath, $payload + [Environment]::NewLine, $utf8NoBom)

Write-Host ""
Write-Host "[1/3] Preparing the manual clip review CSV..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m backend.app.manual_clip $jsonPath --output $csvPath
if ($LASTEXITCODE -ne 0) { throw "Manual clip preparation failed." }

Write-Host ""
Write-Host "[2/3] Running a dry-run. No video will be rendered yet..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m backend.app.batch_render $csvPath --media $mediaPath --approve 1 --output-dir $reportRoot
if ($LASTEXITCODE -ne 0) { throw "Dry-run failed. Review the error before continuing." }

Write-Host ""
Write-Host "Review the selected source and time range above." -ForegroundColor Cyan
Write-Host "The next step creates one MP4 locally. It does not upload or publish it."
$confirm = Read-Host "Do you own or have permission to edit and publish this exact recording, and approve this clip? Type RENDER to continue"
if ($confirm -cne "RENDER") {
    Write-Host "Stopped safely. Your JSON and CSV review files are saved here: $sessionDir" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "[3/3] Rendering approved clip locally..." -ForegroundColor Green
& $pythonExe @pythonPrefix -m backend.app.batch_render $csvPath --media $mediaPath --approve 1 --output-dir $reportRoot --execute --confirm-rights
if ($LASTEXITCODE -ne 0) { throw "Rendering failed. Inspect the report in $reportRoot." }

Write-Host ""
Write-Host "Finished. Open the rendered MP4 and review it manually before any distribution." -ForegroundColor Green
Write-Host "Session files: $sessionDir"
