# System Architecture

## Current local MVP

```text
Synthetic / Permitted Chat JSON
             |
             v
Timezone + Source Validation
             |
             v
Permission Scope / Expiry / Revocation Check
             |
             v
Idempotent Event Normalization
             |
             v
Rolling Chat-Rate Spike Detector
             |
             v
Explainable Candidate Clip Plan
             |
             v
Human Review
             |
             v
Local Authorized Media File
             |
             v
Rights Confirmation + Local FFmpeg Renderer
             |
             v
Local MP4 for Review (no publishing)
```

## Planned next layers

- Provider adapter interface and official YouTube Live Chat API integration
- OAuth authorization handled by the owner
- Persistent consent registry with revocation
- Measured stream/video clock synchronization
- AI context scoring and captions, behind provider adapters and quota limits
- Dashboard, authenticated API, database, queue, and storage
- Human approval workflow
- Optional publishing adapters only after platform permissions and rights checks

## Data boundaries

1. A chat API or metadata API is not assumed to provide raw video access.
2. A source adapter must document its official permission and API scope.
3. Video input must be a local operator-owned or explicitly authorized file.
4. Store the least data needed; avoid retaining full chat histories by default.
5. Keep credentials server-side and never put tokens in browser code, logs, commits, or screenshots.
6. Chat timestamps are not video offsets. A synchronization offset must be measured before generating video cut positions from chat activity.

## Reliability and safety

- bounded retries with backoff and jitter
- queue limits and backpressure
- idempotency keys for ingestion
- explicit permission expiry and revocation checks
- clear states: pending, processing, needs_review, approved, rejected, failed
- manual pause/stop control
- no automatic code edits to the production branch
- no publishing by default
