$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repoRoot

function Read-ClipSeconds([string]$Prompt) {
    while ($true) {
        $raw = Read-Host $Prompt
        $value = 0.0
        $ok = [double]::TryParse($raw, [System.Globalization.NumberStyles]::Float,
            [System.Globalization.CultureInfo]::InvariantCulture, [ref]$value)
        if ($ok -and -not [double]::IsNaN($value) -and -not [double]::IsInfinity($value)) { return $value }
        Write-Host "Enter a valid number of seconds, for example 125.5." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "THE ARO GTA 6 Clip Engine | Local clip session" -ForegroundColor Cyan
Write-Host "Use only a recording you own or are authorized to edit and publish."
Write-Host "You can queue up to 50 moments from the same video in one session."
Write-Host "Nothing is downloaded, uploaded, or published automatically."
Write-Host ""

$pythonExe = $null
$pythonPrefix = @()

# Prefer the Windows Python launcher and let it select an installed Python 3.x.
# The version check enforces 3.11+ without requiring exactly Python 3.11.
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
        if ($LASTEXITCODE -eq 0) {
            $pythonExe = $python.Source
            $pythonPrefix = @()
        }
    }
}

if (-not $pythonExe) {
    throw "Python 3.11+ not found. Install Python 3.11 or newer and enable the Python launcher or Add to PATH."
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw "FFmpeg is missing from PATH. Install FFmpeg and reopen this window." }
if (-not (Get-Command ffprobe -ErrorAction SilentlyContinue)) { throw "ffprobe is missing from PATH. Install FFmpeg including ffprobe and reopen this window." }

$mediaInput = Read-Host "Full path to your authorized local video"
if ([string]::IsNullOrWhiteSpace($mediaInput)) { throw "No video path supplied." }
# Explorer drag-and-drop and copied file paths are often wrapped in quotes.
# Accept either quoted or unquoted paths before checking the actual file.
$mediaInput = $mediaInput.Trim().Trim([char[]](34, 39)).Trim()
if ([string]::IsNullOrWhiteSpace($mediaInput)) { throw "No video path supplied." }
if (-not (Test-Path -LiteralPath $mediaInput -PathType Leaf)) { throw "The selected local video file does not exist." }
$mediaPath = (Resolve-Path -LiteralPath $mediaInput).Path

$videoStream = (& ffprobe -v error -select_streams v:0 -show_entries stream=codec_type -of csv=p=0 $mediaPath | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $videoStream -ne "video") { throw "The selected file has no readable video stream." }
$durationText = (& ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $mediaPath | Out-String).Trim()
$mediaDuration = 0.0
if ($LASTEXITCODE -ne 0 -or -not [double]::TryParse($durationText, [System.Globalization.NumberStyles]::Float,
    [System.Globalization.CultureInfo]::InvariantCulture, [ref]$mediaDuration) -or
    [double]::IsNaN($mediaDuration) -or [double]::IsInfinity($mediaDuration) -or $mediaDuration -le 0) {
    throw "Could not read a finite, positive video duration."
}
Write-Host ("Actual video duration: {0:N2} seconds" -f $mediaDuration) -ForegroundColor Gray

$clips = [System.Collections.Generic.List[object]]::new()
while ($true) {
    if ($clips.Count -ge 50) { Write-Host "Maximum of 50 clips reached." -ForegroundColor Yellow; break }
    $number = $clips.Count + 1
    Write-Host ""
    Write-Host ("--- Clip {0} ---" -f $number) -ForegroundColor Cyan
    $start = Read-ClipSeconds "Start time in seconds"
    $end = Read-ClipSeconds "End time in seconds"
    if ($start -lt 0 -or $end -le $start) { throw "Clip $number range must satisfy 0 <= start < end." }
    if (($end - $start) -gt 180) { throw "Clip $number is longer than 180 seconds." }
    if ($end -gt $mediaDuration) { throw "Clip $number ends beyond the actual video duration." }
    $note = Read-Host "Moment note (optional)"
    if ([string]::IsNullOrWhiteSpace($note)) { $note = "Manually selected moment; review before sharing." }
    $clips.Add(@{ start_seconds = $start; end_seconds = $end; note = $note })
    if ($clips.Count -ge 50) { break }
    $more = Read-Host "Add another moment from this video? (Y/N)"
    if ($more -notmatch "^(y|yes)$") { break }
}

$verticalArgs = @()
$verticalChoice = Read-Host "Create vertical 1080x1920 (9:16) Shorts output with a blurred background? (Y/N, default Y)"
if ([string]::IsNullOrWhiteSpace($verticalChoice) -or $verticalChoice -match "^(?i:y|yes)$") {
    $verticalArgs = @("--vertical")
}

$sessionRoot = Join-Path $repoRoot "manual_clip_sessions"
New-Item -ItemType Directory -Path $sessionRoot -Force | Out-Null
$stamp = (Get-Date -Format "yyyyMMdd_HHmmss") + "_" + [guid]::NewGuid().ToString("N").Substring(0,8)
$sessionDir = Join-Path $sessionRoot $stamp
New-Item -ItemType Directory -Path $sessionDir -ErrorAction Stop | Out-Null
$jsonPath = Join-Path $sessionDir "manual_clips.json"
$csvPath = Join-Path $sessionDir "manual_clips.csv"
$reportRoot = Join-Path $sessionDir "rendered"
$reviewHtml = Join-Path $sessionDir "review.html"
$payload = @{
    source_id = [System.IO.Path]::GetFileName($mediaPath)
    clips = @($clips.ToArray())
} | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText($jsonPath, $payload + [Environment]::NewLine, ([System.Text.UTF8Encoding]::new($false)))

$approvedRows = (1..$clips.Count) -join ","
Write-Host ""
Write-Host ("[1/3] Preparing {0} clip candidate(s)..." -f $clips.Count) -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m backend.app.manual_clip $jsonPath --output $csvPath
if ($LASTEXITCODE -ne 0) { throw "Clip-plan generation failed." }

Write-Host ""
Write-Host "[2/3] Running dry-run. No video is rendered..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m backend.app.batch_render $csvPath --media $mediaPath --approve $approvedRows --output-dir $reportRoot @verticalArgs
if ($LASTEXITCODE -ne 0) { throw "Dry-run failed. No render was started." }

Write-Host ""
Write-Host "Review every listed time range and the exact source file." -ForegroundColor Cyan
$renderChoice = Read-Host "After reviewing the dry-run, type RENDER to continue (anything else stops)"
if ($renderChoice -cne "RENDER") {
    Write-Host "Stopped safely. No video was rendered. Session files: $sessionDir" -ForegroundColor Yellow
    exit 0
}

Write-Host "Only continue if you have rights to edit and distribute this exact recording and have checked embedded third-party content." -ForegroundColor Yellow
$rightsChoice = Read-Host "Type I CONFIRM RIGHTS to authorize this local render"
if ($rightsChoice -cne "I CONFIRM RIGHTS") {
    Write-Host "Stopped safely. No video was rendered." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host ("[3/3] Rendering {0} approved clip(s) locally..." -f $clips.Count) -ForegroundColor Green
& $pythonExe @pythonPrefix -m backend.app.batch_render $csvPath --media $mediaPath --approve $approvedRows --output-dir $reportRoot @verticalArgs --execute --confirm-rights
if ($LASTEXITCODE -ne 0) { throw "Rendering failed. Inspect the session report: $sessionDir" }

$latestRun = Get-ChildItem -LiteralPath $reportRoot -Directory |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (-not $latestRun) { throw "Render completed but its report folder could not be located: $reportRoot" }
$renderReport = Join-Path $latestRun.FullName "batch_render_report.json"
if (-not (Test-Path -LiteralPath $renderReport -PathType Leaf)) {
    throw "Render completed but its batch report is missing: $renderReport"
}

& $pythonExe @pythonPrefix -m backend.app.review_dashboard $renderReport --output $reviewHtml --title "THE ARO Clip Review"
if ($LASTEXITCODE -ne 0) { throw "Clips rendered, but review dashboard generation failed. Report: $renderReport" }

Write-Host ""
Write-Host "Done. Review each MP4 in the session folder before sharing." -ForegroundColor Green
Write-Host "Session folder: $sessionDir"
Write-Host "Review dashboard: $reviewHtml"
Start-Process -FilePath $reviewHtml
