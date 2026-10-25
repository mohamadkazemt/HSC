from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.dependent_service import (
    apply_change_request,
    build_diff,
    create_change_request,
    is_valid_national_code,
    normalize_mobile,
    validate_dependent_data,
)
from accounts.models import Dependent, DependentChangeRequest, UserProfile


ADULT_PAYLOAD = {
    'first_name': 'علی',
    'last_name': 'احمدی',
    'father_name': 'حسن',
    'national_code': '0499370899',
    'birth_certificate_number': '123',
    'birth_date': '1990-05-10',
    'gender': 'male',
    'mobile': '09121234567',
    'relationship': 'فرزند',
    'marital_status': 'married',
    'address': 'تهران، خیابان ولیعصر',
    'education_status': 'graduated',
    'education_level': 'bachelor',
    'field_of_study': 'مهندسی کامپیوتر',
    'study_place': 'دانشگاه تهران',
    'job': 'کارمند',
    'military_status': 'served',
}


class ValidationTests(TestCase):
    def test_national_code_checksum(self):
        self.assertTrue(is_valid_national_code('0499370899'))
        self.assertFalse(is_valid_national_code('0499370898'))
        self.assertFalse(is_valid_national_code('1111111111'))

    def test_normalize_mobile_accepts_persian_digits(self):
        self.assertEqual(normalize_mobile('۰۹۱۲۱۲۳۴۵۶۷'), '09121234567')
        self.assertEqual(normalize_mobile('+989121234567'), '09121234567')

    def test_adult_male_requires_every_field(self):
        cleaned, errors = validate_dependent_data(ADULT_PAYLOAD)
        self.assertEqual(errors, {})
        self.assertEqual(cleaned['military_status'], 'served')

    def test_adult_male_missing_military_and_job(self):
        payload = dict(ADULT_PAYLOAD, military_status='', job='')
        _, errors = validate_dependent_data(payload)
        self.assertIn('military_status', errors)
        self.assertIn('job', errors)

    def test_adult_female_does_not_need_military(self):
        payload = dict(ADULT_PAYLOAD, gender='female', military_status='')
        cleaned, errors = validate_dependent_data(payload)
        self.assertEqual(errors, {})
        self.assertIsNone(cleaned['military_status'])

    def test_minor_does_not_need_adult_fields(self):
        payload = dict(
            ADULT_PAYLOAD,
            birth_date='2015-01-01',
            gender='male',
            marital_status='',
            mobile='',
            address='',
            job='',
            military_status='',
            education_status='studying',
            education_level='primary',
            field_of_study='عمومی',
            study_place='مدرسه شهید بهشتی',
        )
        _, errors = validate_dependent_data(payload)
        self.assertEqual(errors, {})

    def test_education_details_required_while_studying(self):
        payload = dict(ADULT_PAYLOAD, field_of_study='', study_place='')
        _, errors = validate_dependent_data(payload)
        self.assertIn('field_of_study', errors)
        self.assertIn('study_place', errors)

    def test_primary_and_middle_do_not_require_field_of_study(self):
        payload = dict(ADULT_PAYLOAD, education_level='primary', field_of_study='', study_place='دبستان رازی')
        cleaned, errors = validate_dependent_data(payload)
        self.assertNotIn('field_of_study', errors)
        self.assertIsNone(cleaned['field_of_study'])

        payload['education_level'] = 'middle'
        cleaned, errors = validate_dependent_data(payload)
        self.assertNotIn('field_of_study', errors)
        self.assertIsNone(cleaned['field_of_study'])

    def test_education_details_ignored_when_no_education(self):
        payload = dict(
            ADULT_PAYLOAD,
            education_status='none',
            education_level='bachelor',
            field_of_study='',
            study_place='',
        )
        cleaned, errors = validate_dependent_data(payload)
        self.assertEqual(errors, {})
        self.assertIsNone(cleaned['education_level'])

    def test_unknown_relationship_rejected(self):
        _, errors = validate_dependent_data(dict(ADULT_PAYLOAD, relationship='دوست'))
        self.assertIn('relationship', errors)


class ChangeRequestTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='person', password='x', first_name='رضا', last_name='رضایی',
        )
        self.profile = UserProfile.objects.create(
            user=self.user, personnel_code='1001', mobile='09120000000',
        )
        self.dependent = Dependent.objects.create(
            personnel=self.profile, first_name='سارا', last_name='رضایی',
            national_code='0499370899', relationship='همسر',
        )

    def test_delete_request_does_not_delete_before_approval(self):
        change = create_change_request(
            self.profile,
            DependentChangeRequest.Action.DELETE,
            {},
            dependent=self.dependent,
        )
        self.assertEqual(change.status, 'pending')
        self.assertTrue(Dependent.objects.filter(pk=self.dependent.pk).exists())

        apply_change_request(change)
        self.assertFalse(Dependent.objects.filter(pk=self.dependent.pk).exists())
        change.refresh_from_db()
        self.assertEqual(change.status, 'approved')

    def test_update_request_applies_after_approval(self):
        cleaned, _ = validate_dependent_data(ADULT_PAYLOAD)
        change = create_change_request(
            self.profile,
            DependentChangeRequest.Action.UPDATE,
            cleaned,
            dependent=self.dependent,
        )
        self.dependent.refresh_from_db()
        self.assertEqual(self.dependent.first_name, 'سارا')

        apply_change_request(change)
        self.dependent.refresh_from_db()
        self.assertEqual(self.dependent.first_name, 'علی')
        self.assertEqual(self.dependent.address, 'تهران، خیابان ولیعصر')

    def test_create_request_applies_after_approval(self):
        cleaned, _ = validate_dependent_data(dict(ADULT_PAYLOAD, national_code='0084575948'))
        change = create_change_request(
            self.profile,
            DependentChangeRequest.Action.CREATE,
            cleaned,
        )
        self.assertIsNone(change.dependent_id)

        apply_change_request(change)
        change.refresh_from_db()
        self.assertIsNotNone(change.dependent_id)
        self.assertEqual(change.dependent.military_status, 'served')

    def test_duplicate_pending_request_is_blocked(self):
        from accounts.dependent_service import ChangeRequestError

        cleaned, _ = validate_dependent_data(ADULT_PAYLOAD)
        create_change_request(
            self.profile, DependentChangeRequest.Action.UPDATE, cleaned,
            dependent=self.dependent,
        )
        with self.assertRaises(ChangeRequestError):
            create_change_request(
                self.profile, DependentChangeRequest.Action.UPDATE, cleaned,
                dependent=self.dependent,
            )

    def test_diff_only_lists_changed_fields(self):
        cleaned, _ = validate_dependent_data(ADULT_PAYLOAD)
        change = create_change_request(
            self.profile, DependentChangeRequest.Action.UPDATE, cleaned,
            dependent=self.dependent,
        )
        rows = build_diff(change.old_data, change.new_data)
        fields = {row['field'] for row in rows}
        self.assertIn('first_name', fields)
        self.assertIn('address', fields)
        self.assertNotIn('national_code', fields)

    def test_snapshot_stores_jalali_ready_iso_date(self):
        self.dependent.birth_date = timezone.datetime(1990, 5, 10).date()
        self.dependent.save()
        change = create_change_request(
            self.profile, DependentChangeRequest.Action.DELETE, {},
            dependent=self.dependent,
        )
        self.assertEqual(change.old_data['birth_date'], '1990-05-10')


class PortalViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='person2', password='x', first_name='مریم', last_name='کریمی',
        )
        self.profile = UserProfile.objects.create(
            user=self.user, personnel_code='2002', mobile='09121111111',
        )
        self.dependent = Dependent.objects.create(
            personnel=self.profile, first_name='امیر', last_name='کریمی',
            national_code='0499370899', relationship='فرزند',
        )

    def _send_code(self):
        sent = {}

        def fake_send(mobile, template_id, parameters, user_id=None, request=None):
            sent['code'] = parameters[0]['Value']
            sent['mobile'] = mobile
            return True

        from django.core.cache import cache

        cache.clear()
        with patch('dashboard.sms_utils.send_template_sms', side_effect=fake_send):
            response = self.client.post(reverse('dependents:send_code'), {
                'personnel_code': '2002', 'mobile': '09121111111',
            })
        self.assertEqual(response.status_code, 200, response.content)
        return sent

    def test_wrong_mobile_rejected(self):
        response = self.client.post(reverse('dependents:send_code'), {
            'personnel_code': '2002', 'mobile': '09129999999',
        })
        self.assertEqual(response.status_code, 400)

    def test_otp_login_and_submit_update_request(self):
        sent = self._send_code()
        response = self.client.post(reverse('dependents:verify_code'), {'code': sent['code']})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        response = self.client.get(reverse('dependents:info'))
        self.assertEqual(response.status_code, 200)

        payload = dict(ADULT_PAYLOAD, relationship='فرزند')
        payload.update({'birth_year': '1369', 'birth_month': '2', 'birth_day': '20'})
        response = self.client.post(reverse('dependents:edit', args=[self.dependent.pk]), payload)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DependentChangeRequest.objects.filter(
            dependent=self.dependent, status='pending', action='update',
        ).exists())
        self.dependent.refresh_from_db()
        self.assertEqual(self.dependent.first_name, 'امیر')

    def test_requires_otp_before_access(self):
        response = self.client.get(reverse('dependents:info'))
        self.assertEqual(response.status_code, 302)

    def test_save_address_updates_profile_directly(self):
        sent = self._send_code()
        self.client.post(reverse('dependents:verify_code'), {'code': sent['code']})
        response = self.client.post(reverse('dependents:info'), {
            'action': 'save_address', 'address': 'اصفهان، خیابان چهارباغ',
        })
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.address, 'اصفهان، خیابان چهارباغ')

    def test_render_edit_page(self):
        sent = self._send_code()
        self.client.post(reverse('dependents:verify_code'), {'code': sent['code']})
        response = self.client.get(reverse('dependents:edit', args=[self.dependent.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ویرایش اطلاعات')
        self.assertContains(response, self.dependent.first_name)

    def test_render_add_page(self):
        sent = self._send_code()
        self.client.post(reverse('dependents:verify_code'), {'code': sent['code']})
        response = self.client.get(reverse('dependents:add'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'افزودن فرد تحت تکفل جدید')


class HrReviewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'a@example.com', 'x')
        self.staff = User.objects.create_user('staff', password='x')
        self.user = User.objects.create_user(
            username='person3', password='x', first_name='حسین', last_name='حسینی',
        )
        self.profile = UserProfile.objects.create(
            user=self.user, personnel_code='3003', mobile='09122222222',
        )
        self.dependent = Dependent.objects.create(
            personnel=self.profile, first_name='زهرا', last_name='حسینی',
            national_code='0499370899', relationship='فرزند',
        )
        cleaned, _ = validate_dependent_data(ADULT_PAYLOAD)
        self.change = create_change_request(
            self.profile, DependentChangeRequest.Action.UPDATE, cleaned,
            dependent=self.dependent,
        )

    def test_non_superuser_cannot_review(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('accounts:dependent_changes'))
        self.assertEqual(response.status_code, 403)

    def test_approve_applies_change_and_notifies(self):
        self.client.force_login(self.admin)
        with patch('accounts.dependent_notifications._send_sms', return_value=True), \
             patch('accounts.dependent_notifications._send_rubika', return_value=True):
            response = self.client.post(
                reverse('accounts:dependent_change_detail', args=[self.change.pk]),
                {'action': 'approve', 'note': 'تایید شد'},
            )
        self.assertEqual(response.status_code, 302)
        self.change.refresh_from_db()
        self.assertEqual(self.change.status, 'approved')
        self.dependent.refresh_from_db()
        self.assertEqual(self.dependent.first_name, 'علی')

    def test_reject_keeps_data_unchanged(self):
        self.client.force_login(self.admin)
        with patch('accounts.dependent_notifications._send_sms', return_value=True), \
             patch('accounts.dependent_notifications._send_rubika', return_value=True):
            self.client.post(
                reverse('accounts:dependent_change_detail', args=[self.change.pk]),
                {'action': 'reject', 'note': 'مدارک ناقص'},
            )
        self.change.refresh_from_db()
        self.assertEqual(self.change.status, 'rejected')
        self.dependent.refresh_from_db()
        self.assertEqual(self.dependent.first_name, 'زهرا')
