# Linux Staging Handoff

This checklist starts from a reviewed source revision. Do not use it against
production until Linux staging has completed every release gate.

## Validation sequence

1. Install and confirm Python 3.12.
2. Create a clean virtual environment and install `requirements.txt`.
3. Provision an isolated PostgreSQL 16 staging database.
4. Start and validate Redis.
5. Run all Django migrations against staging only.
6. Run `collectstatic` and validate the staged static root.
7. Configure every active GymContract tariff and billing policy explicitly.
8. Assign and verify financial permissions and GymOperator mappings.
9. Run the billing readiness check.
10. Run the Gym Referral health check.
11. Start Gunicorn with the reviewed repository command.
12. Validate Gunicorn Unix socket ownership and permissions.
13. Start Nginx with the reviewed proxy/static configuration.
14. Validate TLS and forwarded scheme behavior.
15. Validate CSRF-protected login and POST operations through Nginx.
16. Validate that QR URLs use the public HTTPS staging host.
17. Start Celery and verify Redis broker consumption/retry/restart behavior.
18. Validate the canonical Rubika webhook with staging credentials only.
19. Run the employee Referral smoke test through Nginx.
20. Verify cross-gym Redeem isolation and one-time usage.
21. Run draft/adjust/finalize/approve Billing smoke tests.
22. Export and inspect Excel output.
23. Run the documented staging backup procedure.
24. Restore into a new PostgreSQL database and rerun health/data checks.
25. Complete and sign the final release gate table.

## Release gates

| Gate | Initial status |
|---|---|
| Python 3.12 installation | NOT VERIFIED ON LINUX |
| Requirements clean install | NOT VERIFIED ON LINUX |
| PostgreSQL 16 | NOT VERIFIED ON LINUX |
| Redis | NOT VERIFIED ON LINUX |
| Migrations | NOT VERIFIED ON LINUX |
| collectstatic and static serving | NOT VERIFIED ON LINUX |
| GymContract tariff/policy | NOT VERIFIED ON LINUX |
| Financial permissions | NOT VERIFIED ON LINUX |
| Billing check | NOT VERIFIED ON LINUX |
| Referral health check | NOT VERIFIED ON LINUX |
| Gunicorn | NOT VERIFIED ON LINUX |
| Unix socket | NOT VERIFIED ON LINUX |
| Nginx | NOT VERIFIED ON LINUX |
| TLS | NOT VERIFIED ON LINUX |
| CSRF through proxy | NOT VERIFIED ON LINUX |
| Public HTTPS QR | NOT VERIFIED ON LINUX |
| Celery | NOT VERIFIED ON LINUX |
| Rubika external webhook | NOT VERIFIED ON LINUX |
| Referral smoke test | NOT VERIFIED ON LINUX |
| Redeem isolation | NOT VERIFIED ON LINUX |
| Billing smoke test | NOT VERIFIED ON LINUX |
| Excel | NOT VERIFIED ON LINUX |
| Backup | NOT VERIFIED ON LINUX |
| Restore drill | NOT VERIFIED ON LINUX |
| Final release gate | NOT VERIFIED ON LINUX |

## Commands to run on Linux

Use environment values supplied by staging infrastructure. Do not substitute
production credentials or databases.

```bash
cd /var/www/HSC
python3.12 --version
python3.12 -m venv venv
venv/bin/pip install -r requirements.txt --no-compile
venv/bin/pip check

DJANGO_SETTINGS_MODULE=HSCprojects.settings.production \
  venv/bin/python manage.py migrate --no-input
DJANGO_SETTINGS_MODULE=HSCprojects.settings.production \
  venv/bin/python manage.py collectstatic --noinput
DJANGO_SETTINGS_MODULE=HSCprojects.settings.production \
  venv/bin/python manage.py check --deploy
DJANGO_SETTINGS_MODULE=HSCprojects.settings.production \
  venv/bin/python manage.py makemigrations --check --dry-run
DJANGO_SETTINGS_MODULE=HSCprojects.settings.production \
  venv/bin/python manage.py check_gym_billing
DJANGO_SETTINGS_MODULE=HSCprojects.settings.production \
  venv/bin/python manage.py check_gym_referrals_health
DJANGO_SETTINGS_MODULE=HSCprojects.settings.production \
  venv/bin/python manage.py test gym_referrals rubika_bot

redis-cli ping
sudo systemd-analyze verify /etc/systemd/system/gunicorn.service
sudo systemd-analyze verify /etc/systemd/system/celery-worker.service
sudo systemd-analyze verify /etc/systemd/system/celery-beat.service
sudo nginx -t
```

Service start/restart, backup and restore commands must follow the reviewed
`DEPLOY.md` and staging infrastructure ownership policy. Before opening traffic,
record command output, smoke-test evidence, backup checksum/size and restored
sample Referral/Invoice identifiers in the release record.

## Stop conditions

Do not proceed toward production if migrations, billing readiness, health,
Referral integrity, Redeem isolation, financial totals, CSRF/TLS, backup restore
or service startup fails.
