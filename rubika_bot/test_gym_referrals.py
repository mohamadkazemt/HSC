from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from accounts.models import Dependent, UserProfile
from gym_referrals.models import Gym, GymContract, GymOperator, Referral
from gym_referrals.services import ReferralService
from rubika_bot.models import GymOperatorState, GymReferralState, RubikaUser
from rubika_bot.services import RubikaBotEngine


class RubikaGymReferralFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('gym-user', first_name='علی', last_name='احمدی')
        self.profile = UserProfile.objects.create(user=self.user, personnel_code='200')
        self.dependent = Dependent.objects.create(
            personnel=self.profile, first_name='سارا', last_name='احمدی',
            national_code='1234567890', relationship='فرزند',
        )
        self.other_user = User.objects.create_user('other-gym-user')
        self.other_profile = UserProfile.objects.create(user=self.other_user)
        self.other_dependent = Dependent.objects.create(
            personnel=self.other_profile, first_name='غریبه', last_name='کاربر',
            national_code='0987654321', relationship='فرزند',
        )
        self.rubika_user = RubikaUser.objects.create(chat_id='gym-chat', user=self.user)
        self.gym_a = Gym.objects.create(name='باشگاه الف', code='BOT-A')
        self.gym_b = Gym.objects.create(name='باشگاه ب', code='BOT-B')
        today = timezone.localdate()
        GymContract.objects.create(gym=self.gym_a, start_date=today - timedelta(days=1), end_date=today + timedelta(days=30))
        GymContract.objects.create(gym=self.gym_b, start_date=today - timedelta(days=1), end_date=today + timedelta(days=30))
        self.engine = RubikaBotEngine(MagicMock())
        self.engine._send_text_message = AsyncMock()

    def call_async(self, method, *args):
        return async_to_sync(method)(*args)

    def start_and_select_self(self):
        self.call_async(self.engine._start_gym_referral, 'gym-chat', self.rubika_user)
        self.call_async(
            self.engine._select_gym_beneficiary, 'gym-chat', self.rubika_user,
            f'gym_beneficiary_EMPLOYEE_{self.profile.pk}',
        )

    def test_complete_employee_flow_creates_referral(self):
        self.start_and_select_self()
        self.call_async(self.engine._select_gym, 'gym-chat', self.rubika_user, f'gym_select_{self.gym_a.pk}')
        self.call_async(self.engine._confirm_gym_referral, 'gym-chat', self.rubika_user)
        referral = Referral.objects.get()
        self.assertEqual(referral.source, Referral.Source.RUBIKA)
        self.assertEqual(referral.gym, self.gym_a)

    def test_active_referral_stops_before_gym_selection(self):
        ReferralService.create_referral(
            requester=self.user, beneficiary_type='EMPLOYEE', beneficiary_id=self.profile.pk,
            gym_id=self.gym_a.pk, source='WEB',
        )
        self.call_async(self.engine._start_gym_referral, 'gym-chat', self.rubika_user)
        self.call_async(self.engine._select_gym_beneficiary, 'gym-chat', self.rubika_user, f'gym_beneficiary_EMPLOYEE_{self.profile.pk}')
        self.assertEqual(GymReferralState.objects.get(rubika_user=self.rubika_user).step, 'active_referral')
        self.assertIn('معرفی‌نامه فعال', self.engine._send_text_message.await_args.args[1])

    def test_manipulated_beneficiary_is_rejected(self):
        self.call_async(self.engine._start_gym_referral, 'gym-chat', self.rubika_user)
        self.call_async(self.engine._select_gym_beneficiary, 'gym-chat', self.rubika_user, f'gym_beneficiary_DEPENDENT_{self.other_dependent.pk}')
        self.assertEqual(Referral.objects.count(), 0)
        self.assertEqual(GymReferralState.objects.get(rubika_user=self.rubika_user).step, 'select_beneficiary')

    def test_valid_dependent_can_create(self):
        self.call_async(self.engine._start_gym_referral, 'gym-chat', self.rubika_user)
        self.call_async(self.engine._select_gym_beneficiary, 'gym-chat', self.rubika_user, f'gym_beneficiary_DEPENDENT_{self.dependent.pk}')
        self.call_async(self.engine._select_gym, 'gym-chat', self.rubika_user, f'gym_select_{self.gym_b.pk}')
        self.call_async(self.engine._confirm_gym_referral, 'gym-chat', self.rubika_user)
        self.assertEqual(Referral.objects.get().beneficiary_account_id, self.dependent.pk)

    def test_inactive_gym_callback_is_rejected(self):
        self.start_and_select_self()
        self.gym_b.is_active = False
        self.gym_b.save(update_fields=('is_active',))
        self.call_async(self.engine._select_gym, 'gym-chat', self.rubika_user, f'gym_select_{self.gym_b.pk}')
        self.assertEqual(Referral.objects.count(), 0)
        self.assertEqual(GymReferralState.objects.get(rubika_user=self.rubika_user).step, 'select_gym')

    def test_expired_contract_callback_is_rejected(self):
        self.start_and_select_self()
        contract = self.gym_b.contracts.get()
        contract.end_date = timezone.localdate() - timedelta(days=1)
        contract.save(update_fields=('end_date',))
        self.call_async(self.engine._select_gym, 'gym-chat', self.rubika_user, f'gym_select_{self.gym_b.pk}')
        self.assertEqual(Referral.objects.count(), 0)

    def test_double_confirm_creates_only_one(self):
        self.start_and_select_self()
        self.call_async(self.engine._select_gym, 'gym-chat', self.rubika_user, f'gym_select_{self.gym_a.pk}')
        self.call_async(self.engine._confirm_gym_referral, 'gym-chat', self.rubika_user)
        self.call_async(self.engine._confirm_gym_referral, 'gym-chat', self.rubika_user)
        self.assertEqual(Referral.objects.count(), 1)

    def test_web_create_between_select_and_confirm_causes_conflict(self):
        self.start_and_select_self()
        self.call_async(self.engine._select_gym, 'gym-chat', self.rubika_user, f'gym_select_{self.gym_b.pk}')
        ReferralService.create_referral(
            requester=self.user, beneficiary_type='EMPLOYEE', beneficiary_id=self.profile.pk,
            gym_id=self.gym_a.pk, source='WEB',
        )
        self.call_async(self.engine._confirm_gym_referral, 'gym-chat', self.rubika_user)
        self.assertEqual(Referral.objects.count(), 1)
        self.assertEqual(Referral.objects.get().gym, self.gym_a)

    def test_legacy_active_is_displayed_and_blocks_creation(self):
        ReferralService.create_referral(
            requester=self.user, beneficiary_type='EMPLOYEE', beneficiary_id=self.profile.pk,
            gym_id=self.gym_a.pk, source='PHYSICAL_LEGACY', legacy_letter_no='OLD-1',
        )
        self.call_async(self.engine._start_gym_referral, 'gym-chat', self.rubika_user)
        self.call_async(self.engine._select_gym_beneficiary, 'gym-chat', self.rubika_user, f'gym_beneficiary_EMPLOYEE_{self.profile.pk}')
        self.assertEqual(Referral.objects.count(), 1)
        self.assertIn('فیزیکی قبلی', self.engine._send_text_message.await_args.args[1])

    def test_employee_and_dependent_are_independent(self):
        ReferralService.create_referral(
            requester=self.user, beneficiary_type='EMPLOYEE', beneficiary_id=self.profile.pk,
            gym_id=self.gym_a.pk, source='WEB',
        )
        self.call_async(self.engine._start_gym_referral, 'gym-chat', self.rubika_user)
        self.call_async(self.engine._select_gym_beneficiary, 'gym-chat', self.rubika_user, f'gym_beneficiary_DEPENDENT_{self.dependent.pk}')
        self.call_async(self.engine._select_gym, 'gym-chat', self.rubika_user, f'gym_select_{self.gym_b.pk}')
        self.call_async(self.engine._confirm_gym_referral, 'gym-chat', self.rubika_user)
        self.assertEqual(Referral.objects.filter(status='ACTIVE').count(), 2)

    def test_rubika_cancel_uses_core_service(self):
        referral = ReferralService.create_referral(requester=self.user, beneficiary_type='EMPLOYEE', beneficiary_id=self.profile.pk, gym_id=self.gym_a.pk, source='WEB')[0]
        self.run_cancel(referral.referral_number)
        referral.refresh_from_db()
        self.assertEqual(referral.status, Referral.Status.CANCELLED)
        self.assertTrue(referral.audit_logs.filter(action='CANCELLED').exists())

    def test_manipulated_cancel_is_rejected(self):
        other_referral = ReferralService.create_referral(requester=self.other_user, beneficiary_type='EMPLOYEE', beneficiary_id=self.other_profile.pk, gym_id=self.gym_a.pk, source='WEB')[0]
        self.call_async(self.engine._ask_cancel_gym_referral, 'gym-chat', self.rubika_user, other_referral.referral_number)
        self.call_async(self.engine._confirm_cancel_gym_referral, 'gym-chat', self.rubika_user)
        other_referral.refresh_from_db()
        self.assertEqual(other_referral.status, Referral.Status.ACTIVE)

    def run_cancel(self, referral_number):
        self.call_async(self.engine._ask_cancel_gym_referral, 'gym-chat', self.rubika_user, referral_number)
        self.call_async(self.engine._confirm_cancel_gym_referral, 'gym-chat', self.rubika_user)


class RubikaGymOperatorFlowTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user('op-worker', first_name='پیمان', last_name='پرسنل')
        self.profile = UserProfile.objects.create(user=self.employee, personnel_code='300')
        self.gym = Gym.objects.create(name='باشگاه اپراتور', code='OP-BOT')
        today = timezone.localdate()
        GymContract.objects.create(gym=self.gym, start_date=today - timedelta(days=1), end_date=today + timedelta(days=30))

        self.operator = User.objects.create_user('op-gymman', first_name='مدیر', last_name='باشگاه')
        self.op_rubika = RubikaUser.objects.create(chat_id='op-chat', user=self.operator)
        GymOperator.objects.create(gym=self.gym, user=self.operator, is_active=True)

        self.referral = ReferralService.create_referral(
            requester=self.employee, beneficiary_type='EMPLOYEE', beneficiary_id=self.profile.pk,
            gym_id=self.gym.pk, source='WEB',
        )[0]

        self.engine = RubikaBotEngine(MagicMock())
        self.engine._send_text_message = AsyncMock()

    def call_async(self, method, *args):
        return async_to_sync(method)(*args)

    def test_operator_keyboard_hides_personnel_sections(self):
        op_keyboard = self.engine._build_command_keyboard(True, operator=True)
        employee_keyboard = self.engine._build_command_keyboard(True, operator=False)
        op_ids = {button.id for row in op_keyboard.rows for button in row.buttons}
        employee_ids = {button.id for row in employee_keyboard.rows for button in row.buttons}
        self.assertIn('my_gym', op_ids)
        self.assertNotIn('payslip', op_ids)
        self.assertNotIn('leave_request', op_ids)
        self.assertNotIn('gym_referrals', op_ids)
        self.assertIn('payslip', employee_ids)
        self.assertIn('gym_referrals', employee_ids)

    def test_welcome_for_operator_is_role_aware(self):
        self.call_async(self.engine._send_welcome, 'op-chat', self.op_rubika)
        text = self.engine._send_text_message.await_args.args[1]
        self.assertIn('مدیر باشگاه', text)
        self.assertNotIn('فیش حقوقی', text)
        self.assertNotIn('مرخصی', text)

    def test_welcome_for_employee_keeps_personnel_text(self):
        employee_rubika = RubikaUser.objects.create(chat_id='emp-op-chat', user=self.employee)
        self.call_async(self.engine._send_welcome, 'emp-op-chat', employee_rubika)
        text = self.engine._send_text_message.await_args.args[1]
        self.assertIn('فیش حقوقی', text)

    def test_personnel_button_is_blocked_for_operator(self):
        self.call_async(self.engine._handle_button, 'op-chat', 'payslip', self.op_rubika)
        text = self.engine._send_text_message.await_args.args[1]
        self.assertIn('مخصوص پرسنل', text)

    def test_personnel_command_is_blocked_for_operator(self):
        self.call_async(self.engine._handle_command, 'op-chat', '/payslip', self.op_rubika)
        text = self.engine._send_text_message.await_args.args[1]
        self.assertIn('مخصوص پرسنل', text)

    def test_verify_code_from_operator_chat(self):
        self.call_async(self.engine._operator_ask_verify, 'op-chat', self.op_rubika, str(self.gym.pk))
        self.assertEqual(GymOperatorState.objects.get(rubika_user=self.op_rubika).step, 'verify_wait')
        self.call_async(self.engine._operator_process_verify, 'op-chat', self.op_rubika, self.referral.referral_number, self.gym.pk)
        text = self.engine._send_text_message.await_args.args[1]
        self.assertIn('استعلام', text)
        self.assertIn(self.referral.referral_number, text)
        self.assertEqual(GymOperatorState.objects.get(rubika_user=self.op_rubika).step, 'idle')

    def test_redeem_from_operator_chat_registers_usage(self):
        self.call_async(self.engine._operator_ask_redeem, 'op-chat', self.op_rubika, str(self.gym.pk))
        self.assertEqual(GymOperatorState.objects.get(rubika_user=self.op_rubika).step, 'redeem_wait')
        self.call_async(self.engine._operator_process_redeem, 'op-chat', self.op_rubika, self.referral.referral_number, self.gym.pk)
        self.referral.refresh_from_db()
        self.assertEqual(self.referral.status, Referral.Status.USED)
        self.assertEqual(self.referral.usage.redeemed_by, self.operator)
        text = self.engine._send_text_message.await_args.args[1]
        self.assertIn('مراجعه', text)

    def test_redeem_foreign_number_is_rejected(self):
        other = Gym.objects.create(name='باشگاه دیگر', code='OP-BOT-2')
        GymContract.objects.create(gym=other, start_date=timezone.localdate() - timedelta(days=1), end_date=timezone.localdate() + timedelta(days=30))
        other_employee = User.objects.create_user('op-other-worker', first_name='دیگر', last_name='پرسنل')
        other_profile = UserProfile.objects.create(user=other_employee, personnel_code='301')
        foreign = ReferralService.create_referral(
            requester=other_employee, beneficiary_type='EMPLOYEE', beneficiary_id=other_profile.pk,
            gym_id=other.pk, source='WEB',
        )[0]
        self.call_async(self.engine._operator_process_redeem, 'op-chat', self.op_rubika, foreign.referral_number, self.gym.pk)
        foreign.refresh_from_db()
        self.assertEqual(foreign.status, Referral.Status.ACTIVE)
        self.assertIsNone(getattr(foreign, 'usage', None))
        text = self.engine._send_text_message.await_args.args[1]
        self.assertIn('باشگاه دیگری', text)
