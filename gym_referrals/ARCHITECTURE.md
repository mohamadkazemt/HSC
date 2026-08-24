# Gym referrals architecture

`accounts.UserProfile` and `accounts.Dependent` remain the source of truth. A
referral stores their local account identifier plus the minimum historical
snapshot needed to keep an issued letter stable.

The invariant `Count(ActiveReferrals per beneficiary) <= 1` is enforced twice:

1. `ReferralService` locks the owning `UserProfile`, expires stale rows and
   checks for an active referral inside one transaction.
2. `one_active_referral_per_beneficiary` is a partial unique database
   constraint. PostgreSQL provides the production guarantee; SQLite also
   supports the partial index used by development and tests.

All web and Rubika entry points call `ReferralService`. Public verification
uses a random UUID token. Sequential referral numbers are display identifiers,
generated with a locked yearly sequence, and are not security credentials.

Effective activity is centralized in `is_referral_active`. Expired ACTIVE rows
are normalized on create and authenticated redeem, avoiding a periodic job
while retaining an explicit EXPIRED state when the row is next touched.

The public QR verification endpoint is deliberately read-only and returns only
the referral number, gym, validity dates and status. It does not expose the
bearer token or beneficiary/account master data and does not create audit
records on a GET request.

Current account data has no explicit dependent eligibility or employment
contract state. Eligibility therefore means an existing owned Account record
and an active Django employee user. This policy should be replaced behind
`resolve_beneficiary` if Account later exposes a stronger status.

Gym operators are explicitly mapped through `GymOperator`. The redeem API
derives the gym from that server-side mapping and never trusts a client gym id.

## Central permission app integration

Page access is additionally gated through the dynamic permissions app
(`PartPermission`, `SectionPermission`, `PositionPermission`,
`UnitGroupPermission`, `UserPermission`). `urls.URLS_WITH_LABELS` registers
eight grantable view names (`gym_referral_create`, `gym_referral_history`,
`gym_referral_management`, `gym_referral_usage`, `gym_manage`,
`gym_contract_manage`, `gym_operator_manage`, `gym_invoice_view`) and
`access.gym_access_required` enforces them. Access passes when the user is a
superuser, holds any Django model permission of this app (existing admin and
operator roles keep working), or has an explicit grant for that view name.
Without one of these, every page including self-service issuance is denied by
default. Public QR verification stays token based and operator redeem keeps
its `GymOperator` authorization; Rubika flows use `ReferralService` directly
and are unaffected by web gating. The sidebar mirrors the same rules through
the `check_permission` template filter.

## Monthly billing

Billing is derived from immutable operational facts, never by duplicating
referral rules. Each contract selects `ISSUED` (the default matching the legacy
business process) or `USED` and stores one decimal price per referral. Invoice
items snapshot that tariff and the display fields at generation time.

Invoices follow `DRAFT -> FINALIZED -> APPROVED -> PAID`; draft/finalized may
also be cancelled. Cancelled item rows remain for audit but become non-billable,
allowing safe regeneration. Conditional unique constraints prevent one issued
referral or one usage from belonging to multiple billable invoices.

For `ISSUED`, `issue_date` is the billing date and referrals already cancelled
when the draft is generated are excluded. For `USED`,
`ReferralUsage.redeemed_at` is the billing date. Contract start and end dates
are inclusive for both policies.
