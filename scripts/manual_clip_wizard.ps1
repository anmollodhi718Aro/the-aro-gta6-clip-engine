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
Write-Host "THE ARO GTA 6 Clip Engine | First local clip" -ForegroundColor Cyan
Write-Host "Use only a recording you own or are authorized to edit and publish."
Write-Host ""

$pythonExe = $null
$pythonPrefix = @()
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    & $py.Source -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" *> $null
    if ($LASTEXITCODE -eq 0) { $pythonExe = $py.Source; $pythonPrefix = @("-3") }
}
if (-not $pythonExe) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" *> $null
        if ($LASTEXITCODE -eq 0) { $pythonExe = $python.Source }
    }
}
if (-not $pythonExe) { throw "Python 3.11+ not found. Install Python and enable the py launcher or Add to PATH." }
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw "FFmpeg is missing from PATH. Install FFmpeg and reopen this window." }
if (-not (Get-Command ffprobe -ErrorAction SilentlyContinue)) { throw "ffprobe is missing from PATH. Install FFmpeg including ffprobe and reopen this window." }

$mediaInput = Read-Host "Full path to your authorized local video"
if ([string]::IsNullOrWhiteSpace($mediaInput)) { throw "No video path supplied." }
$mediaPath = (Resolve-Path -LiteralPath $mediaInput).Path
if (-not (Test-Path -LiteralPath $mediaPath -PathType Leaf)) { throw "The selected path is not a file." }

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

$start = Read-ClipSeconds "Clip start in seconds"
$end = Read-ClipSeconds "Clip end in seconds"
if ($start -lt 0 -or $end -le $start) { throw "Range must satisfy 0 <= start < end." }
if (($end - $start) -gt 180) { throw "Clip must be 180 seconds or shorter." }
if ($end -gt $mediaDuration) { throw "Clip end exceeds the actual video duration." }
$formatChoice = Read-Host "Create vertical 9:16 Short/Reel output? (Y/n)"
$renderOptions = @()
if ([string]::IsNullOrWhiteSpace($formatChoice) -or $formatChoice -match "^(y|yes)$") {
    $renderOptions = @("--vertical")
}

$note = Read-Host "Moment note (optional)"
if ([string]::IsNullOrWhiteSpace($note)) { $note = "Manually selected moment; review before sharing." }

$sessionRoot = Join-Path $repoRoot "manual_clip_sessions"
New-Item -ItemType Directory -Path $sessionRoot -Force | Out-Null
$stamp = (Get-Date -Format "yyyyMMdd_HHmmss") + "_" + [guid]::NewGuid().ToString("N").Substring(0,8)
$sessionDir = Join-Path $sessionRoot $stamp
New-Item -ItemType Directory -Path $sessionDir -ErrorAction Stop | Out-Null
$jsonPath = Join-Path $sessionDir "manual_clips.json"
$csvPath = Join-Path $sessionDir "manual_clips.csv"
$reportRoot = Join-Path $sessionDir "rendered"
$payload = @{
    source_id = [System.IO.Path]::GetFileName($mediaPath)
    clips = @(@{ start_seconds = $start; end_seconds = $end; note = $note })
} | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText($jsonPath, $payload + [Environment]::NewLine, ([System.Text.UTF8Encoding]::new($false)))

Write-Host ""
Write-Host "[1/3] Preparing clip plan..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m backend.app.manual_clip $jsonPath --output $csvPath
if ($LASTEXITCODE -ne 0) { throw "Clip-plan generation failed." }

Write-Host ""
Write-Host "[2/3] Running dry-run. No video is rendered..." -ForegroundColor Yellow
& $pythonExe @pythonPrefix -m backend.app.batch_render $csvPath --media $mediaPath --approve 1 --output-dir $reportRoot @renderOptions
if ($LASTEXITCODE -ne 0) { throw "Dry-run failed. No render was started." }

Write-Host ""
Write-Host "Review the exact file and time range above." -ForegroundColor Cyan
$confirm = Read-Host "Do you have rights to edit and publish this exact recording? Type RENDER to create the local MP4"
if ($confirm -cne "RENDER") {
    Write-Host "Stopped safely. Session files: $sessionDir" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "[3/3] Rendering locally..." -ForegroundColor Green
& $pythonExe @pythonPrefix -m backend.app.batch_render $csvPath --media $mediaPath --approve 1 --output-dir $reportRoot @renderOptions --execute --confirm-rights
if ($LASTEXITCODE -ne 0) { throw "Rendering failed. Inspect the session report: $sessionDir" }
Write-Host ""
Write-Host "Done. Watch the MP4 and review all rights before sharing." -ForegroundColor Green
Write-Host "Session folder: $sessionDir"
