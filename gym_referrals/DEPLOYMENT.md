# Gym referrals production deployment

1. Have the DBA/Infrastructure owner run the production backup procedure and
   verify a restore into an isolated database. The repository does not define
   the production database host, backup storage or retention, so no
   vendor-specific command is assumed.
2. Deploy the reviewed application code without running migrations implicitly.
3. Run `python manage.py migrate gym_referrals` and `python manage.py migrate rubika_bot`.
4. Review every existing gym contract.
5. Set `billing_policy` explicitly (`ISSUED` is the migration default).
6. Set a positive `price_per_referral`; migrated contracts initially have zero.
7. Run `python manage.py check_gym_billing` until it succeeds.
8. Restart the web application.
9. Restart Celery workers and Celery beat.
10. Restart the separate Rubika bot service, if deployed separately.
11. Run `python manage.py check_gym_referrals_health` and application smoke tests.
12. Generate a test referral for an authorized test account.
13. Verify it through its public-token URL/QR.
14. Redeem it as an operator mapped to the correct gym.
15. Generate a test draft invoice for a controlled period.
16. Compare item tariff snapshots and totals with the applicable contract.
17. Do not finalize a real invoice until finance validates contracts, candidates and totals.

Rollback requires restoring the database backup when a schema rollback would
lose post-deployment business data. Do not fake reverse financial transitions.

## Release gates

Do not open write traffic until migrations, `check_gym_billing`,
`check_gym_referrals_health`, referral/QR/redeem smoke tests and a controlled
draft invoice/Excel comparison all pass. A zero tariff is a hard financial
go-live failure. Migration `0004` contains a snapshot backfill with a no-op
reverse; rollback after new writes must use the verified database backup rather
than reverse migrations.
