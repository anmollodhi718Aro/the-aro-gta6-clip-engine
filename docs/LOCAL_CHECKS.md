# Local and CI validation

GitHub Actions validates the Python suite on Ubuntu and the Windows clipping entry points on a Windows runner.

## Windows PowerShell

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_project.ps1
powershell -ExecutionPolicy Bypass -File scripts/smoke_test_render.ps1
```

The project check requires Python 3.11+, compiles backend/tests/Studio, runs the complete unittest suite, and reports FFmpeg/ffprobe availability. The synthetic render smoke test requires FFmpeg with the `libx264` encoder and ffprobe. It creates generated test-pattern footage and verifies both source-aspect landscape output and 1080x1920 vertical output. It does not use creator footage.

The Windows GitHub Actions job installs FFmpeg, runs the project checks, and runs the same synthetic landscape/vertical smoke test.

## Linux / macOS / Git Bash

```bash
bash scripts/check_project.sh
```

This compiles backend, tests and the single-file dashboard, then runs the complete unittest discovery suite. FFmpeg is required only for actual local MP4 rendering.

A successful local or CI run must be tied to the exact commit SHA and its recorded final test summary. A job that fails before runner assignment or before its first step is not a passing test result and is not evidence of an application test failure. Do not mark validation as passed until the relevant job actually executes and completes successfully.
