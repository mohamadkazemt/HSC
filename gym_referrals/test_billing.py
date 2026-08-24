from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile
from .billing import BillingError, GymInvoiceService
from .models import Gym, GymContract, GymInvoice, GymInvoiceItem, Referral
from .services import ReferralService


class GymInvoiceServiceTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_superuser('finance', password='x')
        self.user = User.objects.create_user('employee', first_name='علی', last_name='احمدی')
        self.profile = UserProfile.objects.create(user=self.user, personnel_code='500')
        self.gym = Gym.objects.create(name='باشگاه مالی', code='FIN')
        today = timezone.localdate()
        self.contract = GymContract.objects.create(
            gym=self.gym, start_date=today.replace(day=1), end_date=today + timedelta(days=365),
            billing_policy=GymContract.BillingPolicy.ISSUED, price_per_referral=Decimal('125000.50'),
        )
        self.referral = ReferralService.create_referral(
            requester=self.user, beneficiary_type='EMPLOYEE', beneficiary_id=self.profile.pk,
            gym_id=self.gym.pk, source='WEB',
        )[0]
        self.year, self.month = today.year, today.month

    def generate(self):
        return GymInvoiceService.generate_invoice(
            contract_id=self.contract.pk, year=self.year, month=self.month, actor=self.staff,
        )

    def test_issued_policy_snapshots_item_and_totals(self):
        invoice = self.generate()
        item = invoice.items.get()
        self.assertEqual(item.unit_price, Decimal('125000.50'))
        self.assertEqual(item.beneficiary_name_snapshot, self.referral.beneficiary_full_name_snapshot)
        invoice.refresh_from_db()
        self.assertEqual(invoice.item_count, 1)
        self.assertEqual(invoice.total_amount, Decimal('125000.50'))

    def test_tariff_change_does_not_change_existing_invoice(self):
        invoice = self.generate()
        self.contract.price_per_referral = Decimal('999999.00')
        self.contract.save(update_fields=('price_per_referral',))
        self.assertEqual(invoice.items.get().unit_price, Decimal('125000.50'))

    def test_used_policy_only_bills_redeemed_referral(self):
        self.contract.billing_policy = GymContract.BillingPolicy.USED
        self.contract.save(update_fields=('billing_policy',))
        with self.assertRaises(BillingError) as caught:
            self.generate()
        self.assertEqual(caught.exception.code, 'NO_BILLABLE_ITEMS')
        ReferralService.redeem(self.referral.public_token, self.staff, self.gym)
        invoice = self.generate()
        item = invoice.items.get()
        self.assertIsNotNone(item.referral_usage_id)
        self.assertIsNotNone(item.usage_date)

    def test_duplicate_active_invoice_is_rejected(self):
        self.generate()
        with self.assertRaises(BillingError) as caught:
            self.generate()
        self.assertEqual(caught.exception.code, 'INVOICE_ALREADY_EXISTS')

    def test_cancelled_invoice_releases_items_for_regeneration(self):
        old = self.generate()
        GymInvoiceService.transition(old.pk, GymInvoice.Status.CANCELLED, self.staff)
        new = self.generate()
        self.assertEqual(new.item_count, 1)
        self.assertFalse(old.items.get().is_billable)

    def test_adjustment_recalculates_total_only_in_draft(self):
        invoice = self.generate()
        GymInvoiceService.set_adjustment(invoice.pk, Decimal('-500.50'), self.staff, 'اصلاح')
        invoice.refresh_from_db()
        self.assertEqual(invoice.total_amount, Decimal('124500.00'))
        GymInvoiceService.transition(invoice.pk, GymInvoice.Status.FINALIZED, self.staff)
        with self.assertRaises(BillingError):
            GymInvoiceService.set_adjustment(invoice.pk, Decimal('1.00'))

    def test_controlled_lifecycle_and_paid_immutability(self):
        invoice = self.generate()
        with self.assertRaises(BillingError):
            GymInvoiceService.transition(invoice.pk, GymInvoice.Status.PAID, self.staff)
        for status in (GymInvoice.Status.FINALIZED, GymInvoice.Status.APPROVED, GymInvoice.Status.PAID):
            invoice = GymInvoiceService.transition(invoice.pk, status, self.staff)
        self.assertIsNotNone(invoice.approved_at)
        self.assertIsNotNone(invoice.paid_at)
        with self.assertRaises(BillingError):
            GymInvoiceService.transition(invoice.pk, GymInvoice.Status.CANCELLED, self.staff)

    def test_cancelled_referral_is_not_billed_under_issued(self):
        ReferralService.cancel(self.referral, self.user, 'لغو')
        with self.assertRaises(BillingError) as caught:
            self.generate()
        self.assertEqual(caught.exception.code, 'NO_BILLABLE_ITEMS')

    def test_item_cannot_be_billed_twice(self):
        first = self.generate()
        GymInvoiceService.transition(first.pk, GymInvoice.Status.FINALIZED, self.staff)
        self.assertEqual(GymInvoiceItem.objects.filter(referral=self.referral, is_billable=True).count(), 1)
