# Zero-Budget Development Plan

## Principle

Start with local, synthetic, and free-tier resources, but treat every free service as quota-limited and subject to its terms. A zero-budget prototype is not the same as a free, always-on production service.

## Suggested order

1. Design and test the data model with synthetic events.
2. Build a deterministic local scoring engine.
3. Use a small authorized media sample for local validation.
4. Add one provider adapter only after its official access rules and quota are confirmed.
5. Add a dashboard after the backend workflow is testable.
6. Estimate ongoing storage, compute, bandwidth, API, and AI costs before enabling hosted processing.

## Resource controls

- hard daily and monthly quota limits
- per-source event and storage limits
- queue limits and automatic pause on quota exhaustion
- no paid API calls without a configured budget and owner approval
- no claim of unlimited free tokens, cloud processing, or uploads

## Device-aware workflow

Keep local development lightweight. Avoid large model downloads and full-length video processing on a constrained laptop. Use short authorized samples and test data first.

## When costs appear

Stop or pause the affected worker, show the owner a clear cost/usage explanation, and require an explicit decision before increasing limits or enabling paid services.
