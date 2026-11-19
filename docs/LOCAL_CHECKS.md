# Local validation

GitHub Actions has previously failed before any job steps were recorded, with no downloadable job log. Until that infrastructure issue is resolved, run the same checks locally from a clone of this repository.

## Windows PowerShell

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_project.ps1
```

## Linux / macOS / Git Bash

```bash
bash scripts/check_project.sh
```

Both scripts:
1. Require Python 3.11 or newer.
2. Compile backend, tests and the single-file dashboard.
3. Run the complete unittest discovery suite.
4. Report whether optional FFmpeg is available.

FFmpeg is required only for actual local MP4 rendering. The core Python test suite uses synthetic data and does not require creator footage.

A successful local run should be recorded with the exact commit SHA and the final test summary. Do not mark CI as passed based only on a local run.
