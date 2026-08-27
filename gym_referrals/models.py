import datetime
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Gym(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=40, unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    account_user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="gym_account", verbose_name="کاربر باشگاه",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class GymContract(models.Model):
    class BillingPolicy(models.TextChoices):
        ISSUED = "ISSUED", "معرفی‌نامه‌های صادرشده"
        USED = "USED", "معرفی‌نامه‌های استفاده‌شده"

    gym = models.ForeignKey(Gym, on_delete=models.PROTECT, related_name="contracts")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    billing_policy = models.CharField(max_length=10, choices=BillingPolicy.choices, default=BillingPolicy.ISSUED)
    price_per_referral = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(end_date__gte=models.F("start_date")), name="gym_contract_dates_valid")
        ]

    def is_valid_on(self, date):
        return self.is_active and self.start_date <= date <= self.end_date

    def billing_readiness_errors(self, period_start=None, period_end=None):
        errors = []
        if not self.is_active:
            errors.append("INACTIVE_CONTRACT")
        if self.billing_policy not in self.BillingPolicy.values:
            errors.append("INVALID_BILLING_POLICY")
        if self.price_per_referral <= 0:
            errors.append("INVALID_CONTRACT_TARIFF")
        if period_start and period_end and (self.start_date > period_end or self.end_date < period_start):
            errors.append("CONTRACT_NOT_VALID_FOR_PERIOD")
        return errors

    def is_billing_ready(self, period_start=None, period_end=None):
        return not self.billing_readiness_errors(period_start, period_end)


class GymOperator(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="operators")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="operated_gyms")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("gym", "user"), name="unique_gym_operator")]


class ReferralSequence(models.Model):
    year = models.PositiveIntegerField(unique=True)
    value = models.PositiveIntegerField(default=0)


class GymInvoiceSequence(models.Model):
    year = models.PositiveIntegerField(unique=True)
    value = models.PositiveIntegerField(default=0)


class Referral(models.Model):
    class BeneficiaryType(models.TextChoices):
        EMPLOYEE = "EMPLOYEE", "پرسنل"
        DEPENDENT = "DEPENDENT", "تحت تکفل"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "فعال"
        USED = "USED", "استفاده‌شده"
        EXPIRED = "EXPIRED", "منقضی"
        CANCELLED = "CANCELLED", "لغوشده"
        INVOICED = "INVOICED", "صورت‌حساب‌شده"

    class Source(models.TextChoices):
        WEB = "WEB", "وب"
        RUBIKA = "RUBIKA", "روبیکا"
        ADMIN = "ADMIN", "مدیریت"
        PHYSICAL_LEGACY = "PHYSICAL_LEGACY", "فیزیکی قدیمی"

    referral_number = models.CharField(max_length=32, unique=True)
    public_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="gym_referrals")
    beneficiary_type = models.CharField(max_length=12, choices=BeneficiaryType.choices)
    beneficiary_account_id = models.PositiveBigIntegerField()
    beneficiary_key = models.CharField(max_length=32, editable=False)
    relation_snapshot = models.CharField(max_length=50, blank=True)
    employee_full_name_snapshot = models.CharField(max_length=301)
    beneficiary_full_name_snapshot = models.CharField(max_length=301)
    personnel_no_snapshot = models.CharField(max_length=30, blank=True)
    gym = models.ForeignKey(Gym, on_delete=models.PROTECT, related_name="referrals")
    issue_date = models.DateField()
    valid_from = models.DateField()
    valid_until = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    source = models.CharField(max_length=20, choices=Source.choices)
    legacy_letter_no = models.CharField(max_length=80, blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="created_gym_referrals")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="cancelled_gym_referrals")
    cancellation_reason = models.CharField(max_length=500, blank=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(check=Q(valid_until__gte=models.F("valid_from")), name="referral_dates_valid"),
            models.UniqueConstraint(fields=("beneficiary_key",), condition=Q(status="ACTIVE"), name="one_active_referral_per_beneficiary"),
            models.UniqueConstraint(fields=("legacy_letter_no",), condition=Q(legacy_letter_no__isnull=False), name="unique_legacy_letter_no"),
        ]
        indexes = [
            models.Index(fields=("beneficiary_account_id", "status", "valid_until")),
            models.Index(fields=("gym", "status")),
            models.Index(fields=("created_at",)),
        ]

    def save(self, *args, **kwargs):
        self.beneficiary_key = f"{self.beneficiary_type}:{self.beneficiary_account_id}"
        super().save(*args, **kwargs)

    def is_active(self, at=None):
        if at is None:
            current = timezone.localdate()
        elif isinstance(at, datetime.datetime):
            current = timezone.localtime(at).date() if timezone.is_aware(at) else at.date()
        elif isinstance(at, datetime.date):
            current = at
        else:
            raise TypeError(f"Unsupported type for is_active: {type(at).__name__}")
        return self.status == self.Status.ACTIVE and self.valid_from <= current <= self.valid_until


class ReferralUsage(models.Model):
    referral = models.OneToOneField(Referral, on_delete=models.PROTECT, related_name="usage")
    gym = models.ForeignKey(Gym, on_delete=models.PROTECT)
    redeemed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    redeemed_at = models.DateTimeField(default=timezone.now)


class ReferralAuditLog(models.Model):
    referral = models.ForeignKey(Referral, on_delete=models.PROTECT, related_name="audit_logs")
    action = models.CharField(max_length=40)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ReferralIdempotencyKey(models.Model):
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.CharField(max_length=100)
    request_fingerprint = models.CharField(max_length=64)
    referral = models.OneToOneField(Referral, on_delete=models.CASCADE, related_name="idempotency_record")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("requester", "key"), name="unique_referral_idempotency_key")]


class GymInvoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "پیش‌نویس"
        FINALIZED = "FINALIZED", "نهایی‌شده"
        APPROVED = "APPROVED", "تأییدشده"
        PAID = "PAID", "پرداخت‌شده"
        CANCELLED = "CANCELLED", "لغوشده"

    invoice_number = models.CharField(max_length=50, unique=True)
    gym = models.ForeignKey(Gym, on_delete=models.PROTECT, related_name="invoices")
    gym_contract = models.ForeignKey(GymContract, on_delete=models.PROTECT, related_name="invoices")
    period_year = models.PositiveSmallIntegerField()
    period_month = models.PositiveSmallIntegerField()
    period_start = models.DateField()
    period_end = models.DateField()
    billing_policy = models.CharField(max_length=10, choices=GymContract.BillingPolicy.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    item_count = models.PositiveIntegerField(default=0)
    subtotal = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    adjustment_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="created_gym_invoices")
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_gym_invoices")
    paid_at = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="paid_gym_invoices")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-period_start", "gym__name")
        constraints = [
            models.CheckConstraint(check=Q(period_month__gte=1, period_month__lte=12), name="gym_invoice_month_valid"),
            models.CheckConstraint(check=Q(period_end__gte=models.F("period_start")), name="gym_invoice_period_valid"),
            models.CheckConstraint(check=Q(total_amount=models.F("subtotal") + models.F("adjustment_amount")), name="gym_invoice_total_consistent"),
            models.UniqueConstraint(
                fields=("gym", "gym_contract", "period_year", "period_month"),
                condition=~Q(status="CANCELLED"), name="unique_active_gym_invoice_period",
            ),
        ]
        indexes = [models.Index(fields=("gym", "period_year", "period_month", "status"))]
        permissions = [
            ("generate_gym_invoice", "Can generate gym invoice"),
            ("finalize_gym_invoice", "Can finalize gym invoice"),
            ("approve_gym_invoice", "Can approve gym invoice"),
            ("mark_gym_invoice_paid", "Can mark gym invoice paid"),
            ("cancel_gym_invoice", "Can cancel gym invoice"),
            ("adjust_gym_invoice", "Can adjust gym invoice"),
            ("export_gym_invoice", "Can export gym invoice"),
        ]

    def __str__(self):
        return self.invoice_number


class GymInvoiceItem(models.Model):
    invoice = models.ForeignKey(GymInvoice, on_delete=models.PROTECT, related_name="items")
    referral = models.ForeignKey(Referral, on_delete=models.PROTECT, related_name="invoice_items")
    referral_usage = models.ForeignKey(ReferralUsage, null=True, blank=True, on_delete=models.PROTECT, related_name="invoice_items")
    beneficiary_account_id = models.PositiveBigIntegerField()
    employee_account_id = models.PositiveBigIntegerField()
    beneficiary_name_snapshot = models.CharField(max_length=301)
    relation_snapshot = models.CharField(max_length=50, blank=True)
    employee_name_snapshot = models.CharField(max_length=301)
    personnel_no_snapshot = models.CharField(max_length=30, blank=True)
    referral_number = models.CharField(max_length=32)
    referral_source = models.CharField(max_length=20, choices=Referral.Source.choices)
    issue_date = models.DateField(null=True, blank=True)
    usage_date = models.DateTimeField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    quantity = models.PositiveSmallIntegerField(default=1)
    line_total = models.DecimalField(max_digits=16, decimal_places=2)
    is_billable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(quantity__gt=0), name="gym_invoice_item_quantity_positive"),
            models.CheckConstraint(check=Q(line_total=models.F("unit_price") * models.F("quantity")), name="gym_invoice_item_total_consistent"),
            models.UniqueConstraint(fields=("referral",), condition=Q(referral_usage__isnull=True, is_billable=True), name="unique_issued_referral_invoice_item"),
            models.UniqueConstraint(fields=("referral_usage",), condition=Q(referral_usage__isnull=False, is_billable=True), name="unique_usage_invoice_item"),
        ]
        indexes = [models.Index(fields=("invoice", "referral_number"))]


class GymInvoiceAuditLog(models.Model):
    invoice = models.ForeignKey(GymInvoice, on_delete=models.PROTECT, related_name="audit_logs")
    action = models.CharField(max_length=30)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
