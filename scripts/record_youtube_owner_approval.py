"""Backward-compatible entry point for recording a YouTube owner approval.

The canonical implementation lives in backend.app.youtube_upload so approval
and upload use the same OAuth identity and rights-registry contracts.
"""
from backend.app.youtube_upload import main


if __name__ == "__main__":
    raise SystemExit(main())
