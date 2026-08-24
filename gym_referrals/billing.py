import calendar
import logging
import uuid
from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from .models import GymContract, GymInvoice, GymInvoiceAuditLog, GymInvoiceItem, GymInvoiceSequence, Referral, ReferralUsage

logger = logging.getLogger(__name__)


class BillingError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


class GymInvoiceService:
    TRANSITIONS = {
        GymInvoice.Status.DRAFT: {GymInvoice.Status.FINALIZED, GymInvoice.Status.CANCELLED},
        GymInvoice.Status.FINALIZED: {GymInvoice.Status.APPROVED, GymInvoice.Status.CANCELLED},
        GymInvoice.Status.APPROVED: {GymInvoice.Status.PAID},
        GymInvoice.Status.PAID: set(),
        GymInvoice.Status.CANCELLED: set(),
    }

    @staticmethod
    def period(year, month):
        try:
            start = date(int(year), int(month), 1)
        except (TypeError, ValueError) as exc:
            raise BillingError("INVALID_PERIOD", "سال یا ماه صورتحساب نامعتبر است.") from exc
        return start, date(start.year, start.month, calendar.monthrange(start.year, start.month)[1])

    @classmethod
    @transaction.atomic
    def generate_invoice(cls, *, contract_id, year, month, actor):
        start, end = cls.period(year, month)
        try:
            contract = GymContract.objects.select_for_update().select_related("gym").get(pk=contract_id)
        except GymContract.DoesNotExist as exc:
            raise BillingError("CONTRACT_NOT_FOUND", "قرارداد باشگاه یافت نشد.") from exc
        readiness = contract.billing_readiness_errors(start, end)
        if "INVALID_CONTRACT_TARIFF" in readiness:
            raise BillingError("INVALID_CONTRACT_TARIFF", "تعرفه قرارداد این باشگاه تعیین نشده است. قبل از صدور صورتحساب، تعرفه قرارداد را ثبت کنید.")
        if readiness:
            raise BillingError("NO_ACTIVE_CONTRACT", "قرارداد معتبر و آماده صورتحساب برای این دوره وجود ندارد.")
        if GymInvoice.objects.filter(
            gym=contract.gym, gym_contract=contract, period_year=start.year,
            period_month=start.month,
        ).exclude(status=GymInvoice.Status.CANCELLED).exists():
            raise BillingError("INVOICE_ALREADY_EXISTS", "برای این قرارداد و دوره صورتحساب وجود دارد.")

        items = []
        price = contract.price_per_referral
        eligible_start = max(start, contract.start_date)
        eligible_end = min(end, contract.end_date)
        if contract.billing_policy == GymContract.BillingPolicy.USED:
            usages = ReferralUsage.objects.select_related("referral").filter(
                gym=contract.gym, redeemed_at__date__gte=eligible_start, redeemed_at__date__lte=eligible_end,
            ).exclude(invoice_items__is_billable=True)
            for usage in usages:
                items.append((usage.referral, usage))
        else:
            referrals = Referral.objects.filter(
                gym=contract.gym, issue_date__gte=eligible_start, issue_date__lte=eligible_end,
            ).exclude(invoice_items__is_billable=True).exclude(status=Referral.Status.CANCELLED)
            for referral in referrals:
                items.append((referral, None))
        if not items:
            raise BillingError("NO_BILLABLE_ITEMS", "برای دوره انتخاب‌شده ردیف قابل صورتحساب وجود ندارد.")
        sequence, _ = GymInvoiceSequence.objects.select_for_update().get_or_create(year=start.year)
        sequence.value += 1
        sequence.save(update_fields=("value",))
        invoice = GymInvoice.objects.create(
            invoice_number=f"GINV-{start.year}-{sequence.value:06d}",
            gym=contract.gym, gym_contract=contract, period_year=start.year, period_month=start.month,
            period_start=start, period_end=end, billing_policy=contract.billing_policy,
            created_by=actor,
        )
        item_rows = [cls._item(invoice, referral, price, usage) for referral, usage in items]
        try:
            GymInvoiceItem.objects.bulk_create(item_rows)
        except IntegrityError as exc:
            logger.warning("Invoice generation conflict gym_id=%s contract_id=%s period=%s-%s", contract.gym_id, contract.pk, start.year, start.month)
            raise BillingError("BILLING_ITEM_ALREADY_INVOICED", "حداقل یک ردیف قبلاً صورتحساب شده است.") from exc
        cls._recalculate_locked(invoice)
        invoice.save(update_fields=("item_count", "subtotal", "total_amount"))
        GymInvoiceAuditLog.objects.create(invoice=invoice, action="GENERATED", actor=actor, metadata={"item_count": len(item_rows)})
        logger.info("Gym invoice generated invoice_id=%s gym_id=%s item_count=%s", invoice.pk, invoice.gym_id, len(item_rows))
        return invoice

    @staticmethod
    def _item(invoice, referral, price, usage=None):
        return GymInvoiceItem(
            invoice=invoice, referral=referral, referral_usage=usage,
            beneficiary_account_id=referral.beneficiary_account_id,
            employee_account_id=referral.employee_id,
            beneficiary_name_snapshot=referral.beneficiary_full_name_snapshot,
            relation_snapshot=referral.relation_snapshot,
            employee_name_snapshot=referral.employee_full_name_snapshot,
            personnel_no_snapshot=referral.personnel_no_snapshot,
            referral_number=referral.referral_number, referral_source=referral.source,
            issue_date=referral.issue_date,
            usage_date=usage.redeemed_at if usage else None,
            unit_price=price, quantity=1, line_total=price,
        )

    @staticmethod
    def _recalculate_locked(invoice):
        subtotal = invoice.items.aggregate(value=Sum("line_total"))["value"] or Decimal("0.00")
        invoice.item_count = invoice.items.count()
        invoice.subtotal = subtotal
        invoice.total_amount = subtotal + invoice.adjustment_amount

    @classmethod
    @transaction.atomic
    def set_adjustment(cls, invoice_id, amount, actor=None, notes=None):
        invoice = GymInvoice.objects.select_for_update().get(pk=invoice_id)
        if invoice.status != GymInvoice.Status.DRAFT:
            raise BillingError("INVOICE_IMMUTABLE", "فقط پیش‌نویس قابل اصلاح است.")
        if not (notes or "").strip():
            raise BillingError("ADJUSTMENT_REASON_REQUIRED", "ثبت علت تعدیل الزامی است.")
        old_amount = invoice.adjustment_amount
        invoice.adjustment_amount = Decimal(amount)
        if notes is not None:
            invoice.notes = notes
        cls._recalculate_locked(invoice)
        invoice.save(update_fields=("item_count", "subtotal", "total_amount", "adjustment_amount", "notes"))
        GymInvoiceAuditLog.objects.create(
            invoice=invoice, action="ADJUSTED", actor=actor,
            metadata={"old_amount": str(old_amount), "new_amount": str(invoice.adjustment_amount), "reason": notes.strip()},
        )
        logger.info("Gym invoice adjusted invoice_id=%s", invoice.pk)
        return invoice

    @classmethod
    @transaction.atomic
    def transition(cls, invoice_id, target_status, actor):
        invoice = GymInvoice.objects.select_for_update().get(pk=invoice_id)
        if target_status not in cls.TRANSITIONS[invoice.status]:
            raise BillingError("INVALID_INVOICE_TRANSITION", "تغییر وضعیت صورتحساب مجاز نیست.")
        if target_status == GymInvoice.Status.FINALIZED and invoice.total_amount <= 0:
            raise BillingError("INVOICE_TOTAL_NOT_POSITIVE", "صورتحساب با مبلغ صفر یا منفی قابل نهایی‌سازی نیست.")
        now = timezone.now()
        invoice.status = target_status
        fields = ["status"]
        if target_status == GymInvoice.Status.APPROVED:
            invoice.approved_at, invoice.approved_by = now, actor
            fields += ["approved_at", "approved_by"]
        elif target_status == GymInvoice.Status.PAID:
            invoice.paid_at, invoice.paid_by = now, actor
            fields += ["paid_at", "paid_by"]
        elif target_status == GymInvoice.Status.CANCELLED:
            invoice.items.update(is_billable=False)
        invoice.save(update_fields=fields)
        GymInvoiceAuditLog.objects.create(invoice=invoice, action=target_status, actor=actor)
        logger.info("Gym invoice transitioned invoice_id=%s gym_id=%s status=%s", invoice.pk, invoice.gym_id, target_status)
        return invoice
