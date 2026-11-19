# Original Commentary Content Studio

The content studio creates a production draft from operator-supplied research notes and original THE ARO commentary. It does not browse, scrape, download, or quote third-party videos.

## Input

Create a JSON file such as:

```json
{
  "working_title": "GTA 6 feature explained",
  "topic": "dynamic weather",
  "original_angle": "How weather can change player decisions",
  "audience": "Hindi-speaking GTA fans",
  "research_notes": [
    {
      "claim": "A factual point checked against the linked source.",
      "source_url": "https://example.com/official-source",
      "aro_commentary": "THE ARO's own explanation and analysis.",
      "visual": "An original diagram comparing weather states."
    }
  ]
}
```

Every factual beat needs a source URL and original commentary. The tool checks that these fields exist, but it does not verify the source or fact-check the claim. The operator must verify them.

## Generate a draft

```bash
python -m backend.app.content_studio research.json --output output/gta6_short.md --json-output output/gta6_short.json
```

The Markdown file contains a voiceover draft, source list, visual plan, description, and pre-upload checklist. The JSON file preserves structured data for future desktop UI integration.

## Visual and publishing rules

Prefer original graphics, diagrams, captions, and gameplay recorded by the channel owner. Use third-party material only when the exact source, intended use, platform, date range, and required attribution are explicitly authorized and separately recorded. A credit line or disclaimer is not permission.

The output always sets `approved_for_upload=false`. Human fact-checking, rights review, editing review, and owner approval remain mandatory. This tool does not upload or publish and does not guarantee monetization.
