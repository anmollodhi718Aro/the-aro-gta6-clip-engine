# Synthetic and unit tests

The suite is designed to run without a GTA recording, YouTube credentials, or network access. Prefer synthetic chat events, temporary SQLite databases, generated JSON fixtures, and mocked subprocess/API boundaries.

`test_end_to_end_pipeline.py` covers synthetic permission-gated chat analysis, measured three-anchor clock mapping, candidate-pack export, explainable scoring, and a non-rendering batch dry-run. It uses a placeholder local file and mocks the renderer; it does not need real GTA footage, FFmpeg, network access, or credentials.

## Requirements

- Python 3.11 or newer
- No mandatory third-party Python dependencies for the standard-library test suite
- FFmpeg is optional; tests that require an installed FFmpeg binary must be explicitly skipped when it is unavailable

## Run on Windows (PowerShell)

From the repository root:

```powershell
python --version
python -m compileall -q backend tests THE_ARO_STUDIO.py
python -m unittest discover -s tests -v
```

Or run the combined local check, including the optional FFmpeg availability check:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_project.ps1
```

## Run on macOS/Linux

```bash
python3 --version
python3 -m compileall -q backend tests THE_ARO_STUDIO.py
python3 -m unittest discover -s tests -v
```

## Synthetic test rules

- Use synthetic timestamps, chat events, consent records, and temporary directories.
- Mock YouTube API calls and FFmpeg subprocesses in unit tests. Do not require live accounts or real media.
- Never download, scrape, or commit GTA footage or other media for tests.
- Any optional media fixture must be owned by the project owner or accompanied by explicit permission for the exact test use.
- Never commit API credentials, OAuth tokens, private chat exports, local databases, or rendered media.
- A test file existing is not evidence that it passed. Record the exact commit, command, Python version, and pass/fail/skip counts for each verification run.
