# Master Plan

## Product vision

THE ARO GTA 6 Clip Engine helps a creator or an authorized editor identify promising moments from GTA 6 livestreams and prepare short clips for review. It is a workflow assistant, not a promise of views or earnings.

## Delivery phases

### Phase 1: 7-day MVP target

The 7-day target is a planning goal, not a delivery guarantee.

1. **Foundation:** repository structure, project rules, environment setup, and a small test harness.
2. **Source registry:** store source identity, owner/contact, permission status, scope, expiry, and revocation status.
3. **Event intake:** accept synthetic or permitted chat/event records with timestamps and source IDs.
4. **Moment scoring:** detect chat-rate spikes against a rolling baseline; combine with keywords only as a secondary signal.
5. **Clip plan:** output candidate start/end timestamps, evidence, confidence, and review status.
6. **Authorized media check:** require an explicitly approved local media asset before rendering.
7. **Validation:** run unit and end-to-end tests with synthetic data or authorized sample media; document gaps.

A live end-to-end test is only possible when an authorized source, permitted interface, and usable video asset are available.

### Phase 2: following 30-day app target

This is a separate target after the MVP, and depends on skills, provider access, budget, device capacity, and policy review.

- responsive web dashboard
- secure account and role model
- backend API, database, queue, and storage
- provider/AI connector registry with quotas and fallback rules
- clip review and approval workflow
- optional Android client after backend behavior is stable
- usage limits, billing architecture, privacy and deletion flows
- monitoring, backups, security review, device testing, and release preparation

Public release is not guaranteed by the schedule. Store eligibility, testing, review, and policy requirements must be checked before submission.

## MVP acceptance criteria

- Invalid or unapproved sources are rejected.
- Event timestamps are validated and normalized.
- A known synthetic chat spike is detected in tests.
- Candidate scores are explainable from recorded signals.
- Clip plans are deterministic for fixed inputs.
- No video is downloaded from a platform or processed without an approved asset.
- No clip is published without an explicit human approval.
- Secrets are not committed.
- The README accurately describes implemented functionality.

## Product guardrails

- Use official APIs or explicitly authorized integrations.
- Respect provider terms, rate limits, quotas, and retention rules.
- Creator permission must be recorded, scoped, time-limited where possible, and revocable.
- Permission from a creator does not automatically clear third-party music, game publisher rights, or other content.
- AI provider usage must be quota-aware; never promise unlimited free processing.
- Default to manual review, with an emergency stop available for future automation.
