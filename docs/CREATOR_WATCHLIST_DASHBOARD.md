# Creator Watchlist Dashboard

Build an offline, self-contained HTML view from the evidence-backed seven-day ranking JSON. No browser framework, external assets, tracking, network calls, media downloads, or publishing are used.

## Generate

```bash
python -m backend.app.creator_watchlist_cli metrics.json --output creator_ranking.json
python -m backend.app.creator_watchlist_dashboard creator_ranking.json --output creator_watchlist.html
```

Open `creator_watchlist.html` locally in a browser. The dashboard escapes report-controlled text, only links HTTPS evidence URLs, and applies a restrictive Content Security Policy. It is a snapshot of supplied metrics, not a live ranking or prediction. It does not grant permission to reuse creator content.
