# Deployment and Release Plan

## Development stages

1. Local prototype with synthetic data.
2. Private test deployment with non-sensitive test accounts.
3. Limited creator pilot with written permissions and manual publishing.
4. Public web release after security, privacy, rights, reliability, and cost reviews.
5. Android release only after backend and mobile workflows are stable.

## CI

GitHub Actions may run formatting, static checks, and tests on pushes and pull requests. It is suitable for CI and small scheduled tasks, not for continuous livestream video processing.

## Production requirements

Before public deployment, document and verify:
- supported hosting region and service limits
- authentication, authorization, and account recovery
- database migrations and backup restore
- secrets management and key rotation
- logging, metrics, alerting, and incident response
- privacy notice, terms, data deletion, and retention
- creator permission and rights complaint workflows
- API/provider terms, quotas, and platform policies
- load, failure, and device testing
- release signing, store declarations, and current store eligibility/review requirements

## Rollback

Every release must have a known previous version, a rollback procedure, and a migration strategy. Do not deploy unreviewed AI-generated changes directly to production.

## Release status

No deployment, store submission, or public launch is currently configured by this repository foundation.
