# Master Plan

## Product vision

THE ARO GTA 6 Clip Engine helps a creator or authorized editor identify promising moments from GTA 6 livestreams and prepare short clips for review. It is a workflow assistant, not a promise of views or earnings.

## Delivery phases

### Phase 1: local MVP

- [x] Repository foundation and project rules
- [x] Permission-aware event models
- [x] Deterministic chat-spike detection
- [x] Synthetic event fixture and local CLI
- [x] Human-review-only candidate output
- [x] Local-only FFmpeg rendering from an authorized media file
- [x] Official YouTube public chat REST page adapter
- [x] One-shot YouTube chat-to-candidate CLI
- [x] Automated unit and CLI tests
- [x] Persistent creator/source consent registry
- [x] Durable chat-event ingestion and resumable REST polling checkpoints
- [x] Configurable quota-aware multi-source scheduler
- [ ] Continuous streamList/gRPC worker and resume handling
- [ ] Scheduler-to-worker orchestration, live API quota calibration, and monitoring
- [ ] Clock synchronization and real source pilot
- [ ] Caption and quality checks

### Phase 2: hosted app

- [ ] Responsive web dashboard
- [ ] Secure account and role model
- [ ] Backend API, database, queue, and storage
- [ ] Provider/AI connector registry with quotas and fallback rules
- [ ] Clip review and approval workflow
- [ ] Cloud worker and observability
- [ ] Privacy, deletion, backup, security, and incident workflows
- [ ] Android client after backend behavior is stable
- [ ] Billing architecture only after costs and eligibility are established
- [ ] Public release review and platform/store compliance

Schedules are targets, not guarantees. Public release depends on owner approvals, service access, policy review, security, costs, and platform review.

## MVP acceptance criteria

- Invalid or unapproved sources are rejected.
- Event timestamps are validated and timezone-aware.
- Duplicate event deliveries do not inflate activity counts.
- A known synthetic chat spike is detected in tests.
- Candidate scores are explainable from recorded signals.
- Clip plans are deterministic for fixed inputs.
- YouTube API access is read-only, bounded, permission-gated, and quota-aware.
- Local video rendering refuses unconfirmed rights, remote URLs, invalid durations, and accidental overwrite.
- No clip is published without explicit human approval.
- Secrets are not committed.
- The README accurately describes implemented functionality.

## Product guardrails

- Use official APIs or explicitly authorized integrations.
- Respect provider terms, rate limits, quotas, and retention rules.
- Creator permission must be recorded, scoped, time-limited where possible, and revocable.
- Permission from a creator does not automatically clear third-party music, game footage, or other intellectual-property rights.
- AI provider usage must be quota-aware; never promise unlimited free processing.
- Default to manual review, with an emergency stop available for future automation.
