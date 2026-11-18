# THE ARO GTA 6 Clip Engine

A creator-first workflow for finding and preparing short highlights from **authorized** GTA 6 livestreams and recordings.

> This repository is the separate GTA 6 project. It is not the ARO History Engine.

## Current status

**Stage:** Project foundation and architecture  
**Not yet implemented:** live monitoring, AI highlight detection, video cutting, dashboard, publishing, or mobile app.

The first milestone is a small, testable MVP that can analyze permitted chat/event data, rank candidate moments, and produce a reviewable clip plan. Video processing will only use footage the operator owns or is authorized to use.

## MVP goals

1. Register a source and record its permission status.
2. Ingest supported metadata and chat events through permitted interfaces.
3. Detect unusual chat activity and score candidate timestamps.
4. Produce a clip decision list for human review.
5. Validate an authorized media asset before any local clip rendering.
6. Keep publishing manual and owner-approved.

## Non-goals for the first MVP

- No scraping, stream ripping, or bypassing platform controls.
- No automatic public uploads.
- No promise of virality, monetization, or unlimited free AI/API usage.
- No always-on cloud service until cost, quotas, security, and reliability are understood.

## Safety and rights

Only use footage and data that you own or have permission to process. Platform APIs and creator permission do not automatically clear music, game footage, or third-party rights. See [Copyright and Permissions](docs/COPYRIGHT_POLICY.md).

## Repository map

- `docs/`: project plan, architecture, security, testing, rights, and deployment notes.
- `backend/`: backend implementation (planned).
- `tests/`: automated tests (planned).

## Development principles

- GitHub is the source of truth.
- Build in small, reviewable commits.
- Keep secrets out of Git; use environment variables and a secrets manager.
- Test with synthetic data or authorized sample assets first.
- Automatic recovery may retry bounded, reversible operations. Code changes and production deployment require owner review.
- Publishing requires an explicit human approval step.

## Getting started

The implementation dependencies and local run instructions will be added with the first executable backend milestone. Start with [the master plan](docs/MASTER_PLAN.md) and [system architecture](docs/SYSTEM_ARCHITECTURE.md).
