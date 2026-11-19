# Subtitle Studio

Subtitle Studio formats an operator-supplied timed transcript into an SRT file and runs deterministic quality checks.

## Quick start

Create a JSON file:

```json
{
  "segments": [
    {
      "start": "00:00:01,000",
      "end": "00:00:03,200",
      "text": "Welcome to THE ARO"
    }
  ]
}
```

Run:

```bash
python -m backend.app.subtitle_studio transcript.json --output output/captions.srt --report output/caption_quality.json
```

## Checks

- Valid SRT timestamps and positive segment duration
- Chronological ordering and overlap warnings
- Maximum two lines and 42 characters per line by default
- Reading speed warning above 20 characters per second

A failed quality check returns exit code 1 while still writing the SRT and report so a human can inspect them. Invalid input returns exit code 2. The tool does not transcribe audio, access video, translate text, or certify caption accuracy. Review every caption against the authorized source before use.
