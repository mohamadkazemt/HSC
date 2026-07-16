from django.test import TestCase, override_settings
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
import tempfile
import os
from unittest.mock import patch

from .models import UserProfile, Section, Part, UnitGroup, Position, DriverLicense
from core.validators import validate_signature_image, validate_image_file


class UsernameOrMobileBackendTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='0012345678',
            password='testpass123',
        )
        UserProfile.objects.create(user=self.user, mobile='09123456789')

    def test_authenticates_by_username(self):
        self.assertEqual(
            authenticate(username='0012345678', password='testpass123'),
            self.user,
        )

    def test_authenticates_by_local_mobile(self):
        self.assertEqual(
            authenticate(username='09123456789', password='testpass123'),
            self.user,
        )

    def test_authenticates_by_international_mobile(self):
        self.assertEqual(
            authenticate(username='+989123456789', password='testpass123'),
            self.user,
        )

    def test_rejects_wrong_password(self):
        self.assertIsNone(
            authenticate(username='09123456789', password='wrong-password')
        )

    def test_rejects_duplicate_mobile(self):
        other = User.objects.create_user(username='other', password='testpass123')
        UserProfile.objects.create(user=other, mobile='09123456789')

        self.assertIsNone(
            authenticate(username='09123456789', password='testpass123')
        )


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'login-otp-tests',
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'login-otp-test-sessions',
    },
})
class LoginOTPTest(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='otp-user',
            password='unused-password',
        )
        UserProfile.objects.create(user=self.user, mobile='09121112233')

    def test_login_page_offers_password_and_otp_modes(self):
        response = self.client.get('/accounts/login/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ورود با رمز')
        self.assertContains(response, 'رمز یک‌بارمصرف')

    @patch('accounts.views.secrets.randbelow', return_value=12345)
    @patch('accounts.views.send_template_sms', return_value=True)
    def test_send_and_verify_otp(self, send_sms, _randbelow):
        send_response = self.client.post(
            '/accounts/login/otp/send/',
            {'mobile': '+989121112233'},
        )

        self.assertEqual(send_response.status_code, 200)
        self.assertTrue(send_response.json()['code_sent'])
        send_sms.assert_called_once()
        self.assertEqual(send_sms.call_args.args[0], '09121112233')

        verify_response = self.client.post(
            '/accounts/login/otp/verify/',
            {'code': '۰۱۲۳۴۵'},
        )

        self.assertEqual(verify_response.status_code, 200)
        self.assertTrue(verify_response.json()['success'])
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.id)
        self.assertNotIn('accounts_login_otp', self.client.session)

    @override_settings(LOGIN_OTP_MAX_ATTEMPTS=2)
    @patch('accounts.views.secrets.randbelow', return_value=12345)
    @patch('accounts.views.send_template_sms', return_value=True)
    def test_otp_is_removed_after_max_attempts(self, _send_sms, _randbelow):
        self.client.post('/accounts/login/otp/send/', {'mobile': '09121112233'})

        first = self.client.post('/accounts/login/otp/verify/', {'code': '999999'})
        second = self.client.post('/accounts/login/otp/verify/', {'code': '999999'})

        self.assertEqual(first.status_code, 400)
        self.assertEqual(second.status_code, 400)
        self.assertNotIn('accounts_login_otp', self.client.session)

    @patch('accounts.views.send_template_sms')
    def test_unknown_mobile_does_not_reveal_account_or_send_sms(self, send_sms):
        response = self.client.post(
            '/accounts/login/otp/send/',
            {'mobile': '09129999999'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(response.json()['code_sent'])
        send_sms.assert_not_called()


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='تست',
            last_name='کاربر'
        )
        
        self.section = Section.objects.create(name='مهندسی')
        self.part = Part.objects.create(name='استخراج', section=self.section)
        self.unit_group = UnitGroup.objects.create(name='گروه اول', part=self.part)
        self.position = Position.objects.create(name='مهندس', unit_group=self.unit_group)
    
    def test_create_user_profile(self):
        """تست ایجاد پروفایل کاربر"""
        profile = UserProfile.objects.create(
            user=self.user,
            personnel_code='12345',
            section=self.section,
            part=self.part,
            unit_group=self.unit_group,
            position=self.position,
            group='A',
            mobile='09123456789'
        )
        
        self.assertEqual(str(profile), 'تست کاربر 12345')
        self.assertEqual(profile.personnel_code, '12345')
        self.assertEqual(profile.group, 'A')
    
    def test_generate_verification_code(self):
        """تست تولید کد تأیید"""
        profile = UserProfile.objects.create(user=self.user)
        profile.generate_verification_code()
        
        self.assertIsNotNone(profile.verification_code)
        self.assertEqual(len(profile.verification_code), 6)
        self.assertTrue(profile.verification_code.isdigit())
        self.assertIsNotNone(profile.code_generated_at)
    
    def create_test_image(self, width=200, height=100, format='PNG'):
        """ایجاد تصویر تست"""
        image = Image.new('RGB', (width, height), color='white')
        buffer = BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        return SimpleUploadedFile(
            f'test_image.{format.lower()}',
            buffer.getvalue(),
            content_type=f'image/{format.lower()}'
        )
    
    def test_signature_validation_valid(self):
        """تست اعتبارسنجی تصویر امضای معتبر"""
        valid_image = self.create_test_image(300, 150)
        
        # نباید خطا بدهد
        try:
            validate_signature_image(valid_image)
        except ValidationError:
            self.fail("validate_signature_image raised ValidationError unexpectedly!")
    
    def test_signature_validation_invalid_ratio(self):
        """تست اعتبارسنجی تصویر امضا با نسبت نامناسب"""
        invalid_image = self.create_test_image(800, 50)  # نسبت خیلی کشیده
        
        with self.assertRaises(ValidationError):
            validate_signature_image(invalid_image)
    
    def test_signature_validation_too_small(self):
        """تست اعتبارسنجی تصویر امضای کوچک"""
        small_image = self.create_test_image(50, 25)
        
        with self.assertRaises(ValidationError):
            validate_signature_image(small_image)


class SectionModelTest(TestCase):
    def test_create_section(self):
        """تست ایجاد بخش"""
        section = Section.objects.create(
            name='مهندسی معدن',
            description='بخش مهندسی معدن'
        )
        
        self.assertEqual(str(section), 'مهندسی معدن')
        self.assertEqual(section.description, 'بخش مهندسی معدن')


class PartModelTest(TestCase):
    def setUp(self):
        self.section = Section.objects.create(name='مهندسی')
    
    def test_create_part(self):
        """تست ایجاد قسمت"""
        part = Part.objects.create(
            name='استخراج',
            section=self.section,
            description='قسمت استخراج'
        )
        
        self.assertEqual(str(part), 'استخراج')
        self.assertEqual(part.section, self.section)


class DriverLicenseModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='driver_test',
            password='testpass123'
        )
    
    def test_create_driver_license(self):
        """تست ایجاد گواهینامه"""
        front_image = self.create_test_image()
        back_image = self.create_test_image()
        
        license = DriverLicense.objects.create(
            user=self.user,
            license_base='2',
            expiry_date='2025-12-31',
            has_special=True,
            special_codes=['38', '39'],
            front_image=front_image,
            back_image=back_image
        )
        
        self.assertEqual(license.license_base, '2')
        self.assertTrue(license.has_special)
        self.assertEqual(license.special_codes, ['38', '39'])
        self.assertIn('پایه دو', str(license))
    
    def test_is_complete_method(self):
        """تست متد is_complete"""
        front_image = self.create_test_image()
        back_image = self.create_test_image()
        
        # گواهینامه کامل
        license = DriverLicense.objects.create(
            user=self.user,
            license_base='1',
            expiry_date='2025-12-31',
            has_special=False,
            front_image=front_image,
            back_image=back_image
        )
        
        self.assertTrue(license.is_complete())
        
        # گواهینامه ناکامل (بدون تاریخ انقضا)
        license.expiry_date = None
        license.save()
        self.assertFalse(license.is_complete())
    
    def create_test_image(self):
        """ایجاد تصویر تست"""
        image = Image.new('RGB', (200, 100), color='white')
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return SimpleUploadedFile(
            'test_license.png',
            buffer.getvalue(),
            content_type='image/png'
        )
