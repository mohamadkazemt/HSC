# Local Release Acceptance

This document freezes the Gym Referral / Rubika / Billing release candidate as
validated in Windows local development. It does not claim Linux or production
infrastructure acceptance.

## Accepted runtime

- Python 3.12.10
- Django 4.2
- PostgreSQL 17.10 for local PostgreSQL rehearsal
- Redis 8.8.0 for local cache, session and Celery integration
- Celery 5.4.0

No direct patches to Python, Django, aiohttp or installed site-packages are
required or permitted by the release runbook.

## Local acceptance results

| Area | Result | Evidence |
|---|---|---|
| Referral Core | PASS | Service, HTTP, invariant and database tests |
| Rubika Adapter / Flow | PASS | Adapter, state, cancellation and race tests |
| Billing | PASS | Lifecycle, snapshots, duplicate protection and preflight |
| Permissions | PASS | Explicit finance permissions and HTTP denial/allow tests |
| QR | PASS | Token URL generation and privacy tests |
| Excel | PASS | Unicode, Decimal, snapshots and formula-injection test |
| Jalali presentation | PASS | Feature regression coverage |
| Redis | PASS | Real local Redis `PING`, cache and reconnect tests |
| Sessions | PASS | Login, persistence and logout with Redis backend |
| Celery | PASS | Real worker enqueue, consume, reconnect and restart tests |
| PostgreSQL 17 local verification | PASS | Migrations, catalog constraints and application smoke tests |
| Concurrency | PASS | Referral, WEB/Rubika, redeem, invoice and sequence races |
| Migration rehearsal | PASS | Pre-feature data preserved through current migrations |
| Backup/restore local PostgreSQL | PASS | Dump restored into a new database and data/checks validated |
| 1,000-item invoice | PASS | Generation, detail and Excel smoke tests |
| 10,000-item migration backfill | PASS | Batched migration completed and snapshots validated |
| Feature tests | PASS | Python 3.12 relevant suites |
| Migration freeze | PASS | `makemigrations --check --dry-run` reports no changes |

## Session restart behavior

**ACCEPTED OPERATIONAL BEHAVIOR:** restarting a non-persistent Redis instance
logs users out. It does not delete or roll back business state:

- Referral records remain in PostgreSQL.
- Invoice records remain in PostgreSQL.
- ReferralUsage records remain in PostgreSQL.
- Rubika flow state remains in PostgreSQL.
- Financial state is not stored in Django sessions.

Operations must either accept re-authentication after Redis restart or provide
and validate an infrastructure persistence policy on Linux staging.

## Accepted known risk

The duplicate `rubika_bot` URL namespace warning remains unchanged for this
freeze. Canonical production documentation uses `/rubika_bot/webhook/`; the
compatibility route must be validated before changing URL registration.

## Known repository test failures

These failures are outside Gym Referral scope and do not invalidate the green
feature suite. They still require ownership and follow-up.

| App | Test/group | Root cause | Gym release impact | Follow-up owner |
|---|---|---|---|---|
| corrective_actions | `test_automation` import | Interactive shell script is discovered as a test and imports `safe_notification` from its old module | No direct impact; runtime Celery tasks import the current module | Corrective Actions owner |
| risk_assessment | validation/model tests | Removed models and stale fixture field names | No direct dependency in Gym flows | Risk Assessment owner |
| BaseInfo | mining machine tests | Stale Contractor fixture fields | Gym uses its own `Gym` model | BaseInfo owner |
| anomalis | image compression tests | Windows console encoding and stale compression expectation | No dependency in Referral/Billing | Anomaly owner |
| meetings | create regression | Fixed date is no longer in the future | No dependency in Gym flows | Meetings owner |

## Deferred to Linux staging

Every item below is deliberately **NOT VERIFIED ON LINUX**:

- PostgreSQL 16 verification
- Gunicorn runtime
- Nginx
- Unix socket permissions
- systemd
- TLS
- real reverse proxy
- Rubika external webhook
- Production backup/restore
- Linux collectstatic serving
- Linux service restart tests

