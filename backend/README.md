# Backend

The local Phase 1 core runs without network access or provider credentials.

- models.py: timezone-aware permission, event, and candidate models.
- registry.py: atomic local JSON source registry with scope and revocation checks.
- ingestion.py: permission-gated UTC normalization, size limits, and deduplication.
- detection.py: deterministic rolling chat-rate spike detector.
- cli.py: candidate-plan generation, optionally using the authoritative source registry.
- review.py and review_cli.py: append-only human review ledger and CLI.
- render.py and render_cli.py: local FFmpeg rendering guarded by registered edit_media permission.

Live platform adapters, AI services, dashboards, OAuth upload, and public publishing are not part of this local MVP.
