# Backend

The backend is implemented as a Python 3.11+ package under `backend/app/`. It uses a standard-library-first design so core logic and synthetic tests can run without live YouTube credentials or GTA footage.

## Current modules

- **Core events and detection:** `models.py`, `detection.py`, `chat_event_store.py`
- **Consent and rights:** `consent_registry.py`, `rights_registry.py`, `content_preflight.py`
- **YouTube chat ingestion:** `youtube_live_chat.py`, `youtube_polling_worker.py`, `youtube_stream_ingestion.py`, `youtube_stream_list_grpc.py`, `youtube_stream_list_worker.py`, `youtube_multi_source_service.py`, `scheduled_ingestion.py`
- **Polling and quota state:** `polling_checkpoint_store.py`, `quota_scheduler.py`
- **Clip planning and rendering:** `clipping.py`, `clock_sync.py`, `clip_pack.py`, `candidate_quality.py`, `output_manager.py`, `batch_render.py`
- **Creator/content tools:** `content_studio.py`, `creator_watchlist.py`, `creator_watchlist_cli.py`, `creator_watchlist_dashboard.py`, `subtitle_studio.py`
- **Interfaces:** `cli.py`, `review_dashboard.py`, `youtube_cli.py`, `youtube_upload.py`

See module docstrings and matching files in `docs/` for behavior and limitations. The local Studio entry point is `THE_ARO_STUDIO.py`.

## Run synthetic checks

From the repository root:

```bash
python3 -m compileall -q backend tests THE_ARO_STUDIO.py
python3 -m unittest discover -s tests -v
```

On Windows, use `python` instead of `python3`, or run `scripts/check_project.ps1`. Python 3.11+ is required. FFmpeg is optional for unit tests and required only for actual local media rendering.

## Development boundaries

- Keep core detection and decision logic testable without network access or provider credentials.
- Mock provider APIs and FFmpeg subprocesses in unit tests; use synthetic events and temporary directories.
- Re-check consent and exact rights scope at ingestion/rendering. Human approval remains required for publishing.
- Process only local media that the operator owns or is explicitly authorized to edit and distribute.
- Do not add stream ripping, platform-control bypasses, fake engagement, or unattended public publishing.
- Never commit OAuth tokens, API credentials, private chat exports, local databases, or rendered media.

## Known product gaps

The repository is not a finished hosted production service. Automatic speech-to-text, automatic visual highlight recognition, automatic sync-marker detection, persistent cloud workers/storage, a packaged Windows installer, and public multi-user security/privacy readiness remain outstanding. The optional YouTube uploader is a manual, dry-run-by-default workflow and requires owner configuration and approval.

See `docs/PROJECT_STATUS.md` and `docs/RELEASE_CANDIDATE.md` for release gates and owner-side setup.
