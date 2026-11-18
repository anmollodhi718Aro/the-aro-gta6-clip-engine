# System Architecture

## Current state

This document describes the intended architecture. The components below are plans until code and tests exist.

## MVP flow

```text
Creator / Source
      |
      v
Permission Registry -----> Reject / Pause / Revoke
      |
      v
Permitted Metadata + Chat/Event Intake
      |
      v
Timestamp Normalizer
      |
      v
Spike Detector + Candidate Scorer
      |
      v
Clip Decision List (timestamps + evidence)
      |
      v
Human Review
      |
      v
Authorized Media Asset Check
      |
      v
Local Clip Renderer (later milestone)
      |
      v
Human-approved export (publishing is out of MVP)
```

## Planned modules

- `backend/app/permissions/`: consent records, scope, expiry, revocation.
- `backend/app/sources/`: source metadata and supported provider adapters.
- `backend/app/ingestion/`: validated event intake.
- `backend/app/detection/`: rolling chat baseline and candidate scoring.
- `backend/app/clipping/`: clip plans first; authorized media rendering later.
- `backend/app/review/`: human review and approval state.
- `backend/app/api/`: future HTTP API.
- `tests/`: unit, integration, and end-to-end tests.

## Data boundaries

1. A chat API or metadata API is not assumed to provide raw video access.
2. A source adapter must document its official permission and API scope.
3. Video input must be an operator-owned file or a media asset with documented authorization.
4. Store the least data needed; avoid retaining full chat histories by default.
5. Keep credentials server-side and never put tokens in browser code, logs, commits, or screenshots.

## Candidate scoring

The initial scorer should be deterministic and explainable. Signals may include:
- chat messages per time window compared with the source's recent baseline
- configurable keyword matches
- repeated audience reactions or relevant event markers
- timestamp confidence and event density

A spike is a candidate, not proof that a moment is entertaining. The system should return evidence and a score breakdown, not label a clip as guaranteed viral.

## Timestamp handling

Use UTC internally and preserve the source timestamp and timezone metadata. Validate ordering and detect missing intervals. Do not infer a video cut window from chat timestamps unless the video and event clocks have been synchronized and the offset is known.

## Reliability

- bounded retries with exponential backoff and jitter
- queue limits and backpressure
- idempotency keys for ingestion
- clear states: pending, processing, needs_review, approved, rejected, failed
- manual pause/stop control
- no automatic code edits to the production branch
