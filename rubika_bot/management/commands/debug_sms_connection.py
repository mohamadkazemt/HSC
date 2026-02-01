"""
دستور مدیریتی برای بررسی لاگ‌های اتصال SMS و تشخیص مشکل

استفاده:
    python manage.py debug_sms_connection --national-code 3090886375 --personnel-code 110326
    python manage.py debug_sms_connection --last 10  # آخرین 10 لاگ خطا
    python manage.py debug_sms_connection --mobile 09123456789  # بررسی SMS برای یک شماره
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from accounts.models import UserProfile
from rubika_bot.models import WebhookLog
from rubika_bot.services import normalize_digits
from datetime import timedelta

try:
    from dashboard.models_sms import SMSLog
    SMS_LOGS_AVAILABLE = True
except ImportError:
    SMS_LOGS_AVAILABLE = False


class Command(BaseCommand):
    help = 'بررسی لاگ‌های اتصال SMS و تشخیص مشکل'

    def add_arguments(self, parser):
        parser.add_argument(
            '--national-code',
            type=str,
            help='کد ملی برای جستجو'
        )
        parser.add_argument(
            '--personnel-code',
            type=str,
            help='کد پرسنلی برای جستجو'
        )
        parser.add_argument(
            '--mobile',
            type=str,
            help='شماره موبایل برای بررسی SMS'
        )
        parser.add_argument(
            '--last',
            type=int,
            default=20,
            help='تعداد آخرین لاگ‌های خطا برای نمایش (پیش‌فرض: 20)'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='ساعت‌های گذشته برای جستجو (پیش‌فرض: 24)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('🔍 بررسی لاگ‌های اتصال SMS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # بررسی با کد ملی و کد پرسنلی
        if options.get('national_code') and options.get('personnel_code'):
            self.check_user_connection(
                options['national_code'],
                options['personnel_code']
            )
        
        # بررسی SMS برای یک شماره
        if options.get('mobile'):
            self.check_sms_logs(options['mobile'], options['hours'])
        
        # نمایش آخرین لاگ‌های خطا
        if not options.get('national_code') and not options.get('mobile'):
            self.show_recent_errors(options['last'], options['hours'])

    def check_user_connection(self, national_code, personnel_code):
        """بررسی اتصال کاربر با کد ملی و کد پرسنلی"""
        self.stdout.write(self.style.WARNING('📋 بررسی کاربر:'))
        self.stdout.write(f'   کد ملی: {national_code}')
        self.stdout.write(f'   کد پرسنلی: {personnel_code}')
        self.stdout.write('')

        # Normalize
        national_code_norm = normalize_digits(national_code)
        personnel_code_norm = normalize_digits(personnel_code)
        
        self.stdout.write(f'   کد ملی normalize شده: {national_code_norm}')
        self.stdout.write(f'   کد پرسنلی normalize شده: {personnel_code_norm}')
        self.stdout.write('')

        # جستجوی کاربر
        from django.db.models import Q
        
        profile = UserProfile.objects.filter(
            Q(national_code=national_code_norm) | Q(national_code=national_code),
            Q(personnel_code=personnel_code_norm) | Q(personnel_code=personnel_code)
        ).select_related('user').first()
        
        if not profile:
            # جستجو با username
            profile = UserProfile.objects.filter(
                Q(user__username=national_code_norm) | Q(user__username=national_code),
                Q(personnel_code=personnel_code_norm) | Q(personnel_code=personnel_code)
            ).select_related('user').first()
        
        if profile:
            self.stdout.write(self.style.SUCCESS('✅ کاربر یافت شد:'))
            self.stdout.write(f'   نام کاربری: {profile.user.username}')
            self.stdout.write(f'   نام: {profile.user.get_full_name()}')
            self.stdout.write(f'   کد ملی در DB: {profile.national_code}')
            self.stdout.write(f'   کد پرسنلی در DB: {profile.personnel_code}')
            self.stdout.write(f'   شماره موبایل: {profile.mobile or "❌ خالی"}')
            
            if profile.mobile:
                mobile_norm = normalize_digits(profile.mobile)
                self.stdout.write(f'   شماره موبایل normalize شده: {mobile_norm}')
            
            self.stdout.write('')
            
            # بررسی لاگ‌های مربوطه
            self.check_related_logs(profile.user.username, profile.mobile)
        else:
            self.stdout.write(self.style.ERROR('❌ کاربر یافت نشد!'))
            self.stdout.write('')
            
            # جستجوی جداگانه
            by_personnel = UserProfile.objects.filter(
                Q(personnel_code=personnel_code_norm) | Q(personnel_code=personnel_code)
            ).first()
            
            if by_personnel:
                self.stdout.write(self.style.WARNING('⚠️ کاربر با این کد پرسنلی یافت شد:'))
                self.stdout.write(f'   نام کاربری: {by_personnel.user.username}')
                self.stdout.write(f'   کد ملی در DB: {by_personnel.national_code}')
                self.stdout.write('')
            
            by_national = UserProfile.objects.filter(
                Q(national_code=national_code_norm) | Q(national_code=national_code) |
                Q(user__username=national_code_norm) | Q(user__username=national_code)
            ).first()
            
            if by_national:
                self.stdout.write(self.style.WARNING('⚠️ کاربر با این کد ملی یافت شد:'))
                self.stdout.write(f'   نام کاربری: {by_national.user.username}')
                self.stdout.write(f'   کد پرسنلی در DB: {by_national.personnel_code}')
                self.stdout.write('')

    def check_sms_logs(self, mobile, hours):
        """بررسی لاگ‌های SMS برای یک شماره"""
        self.stdout.write(self.style.WARNING(f'📱 بررسی SMS برای شماره: {mobile}'))
        self.stdout.write('')
        
        mobile_norm = normalize_digits(mobile)
        if not mobile_norm.startswith('0'):
            if mobile_norm.startswith('98'):
                mobile_norm = '0' + mobile_norm[2:]
            elif len(mobile_norm) == 10:
                mobile_norm = '0' + mobile_norm
        
        self.stdout.write(f'   شماره normalize شده: {mobile_norm}')
        self.stdout.write('')
        
        if not SMS_LOGS_AVAILABLE:
            self.stdout.write(self.style.ERROR('❌ ماژول SMS logs در دسترس نیست'))
            return
        
        cutoff = timezone.now() - timedelta(hours=hours)
        logs = SMSLog.objects.filter(
            mobile_number__in=[mobile, mobile_norm]
        ).filter(
            created_at__gte=cutoff
        ).order_by('-created_at')[:20]
        
        if logs:
            self.stdout.write(self.style.SUCCESS(f'✅ {len(logs)} لاگ SMS یافت شد:'))
            self.stdout.write('')
            for log in logs:
                status_icon = '✅' if log.status == 'sent' else '❌' if log.status == 'failed' else '⏳'
                self.stdout.write(f'{status_icon} [{log.created_at.strftime("%Y-%m-%d %H:%M:%S")}]')
                self.stdout.write(f'   وضعیت: {log.status}')
                self.stdout.write(f'   قالب: {log.template_id}')
                if log.error_message:
                    self.stdout.write(f'   خطا: {log.error_message}')
                self.stdout.write('')
        else:
            self.stdout.write(self.style.WARNING('⚠️ لاگ SMS یافت نشد'))

    def check_related_logs(self, username, mobile):
        """بررسی لاگ‌های مربوط به کاربر"""
        self.stdout.write(self.style.WARNING('📋 بررسی لاگ‌های مربوطه:'))
        self.stdout.write('')
        
        # Webhook logs
        cutoff = timezone.now() - timedelta(hours=24)
        webhook_logs = WebhookLog.objects.filter(
            Q(message__icontains=username) | 
            Q(message__icontains=mobile) |
            Q(data__icontains=username) |
            Q(data__icontains=mobile)
        ).filter(
            created_at__gte=cutoff
        ).order_by('-created_at')[:10]
        
        if webhook_logs:
            self.stdout.write(self.style.SUCCESS(f'✅ {len(webhook_logs)} لاگ Webhook یافت شد:'))
            for log in webhook_logs:
                log_type_icon = {
                    'error': '❌',
                    'info': 'ℹ️',
                    'outgoing': '📤',
                    'incoming': '📥'
                }.get(log.log_type, '📋')
                
                self.stdout.write(f'{log_type_icon} [{log.created_at.strftime("%Y-%m-%d %H:%M:%S")}] {log.title}')
                self.stdout.write(f'   {log.message[:200]}')
                self.stdout.write('')
        else:
            self.stdout.write(self.style.WARNING('⚠️ لاگ Webhook یافت نشد'))
            self.stdout.write('')

    def show_recent_errors(self, limit, hours):
        """نمایش آخرین لاگ‌های خطا"""
        self.stdout.write(self.style.WARNING(f'❌ آخرین {limit} لاگ خطا (آخرین {hours} ساعت):'))
        self.stdout.write('')
        
        cutoff = timezone.now() - timedelta(hours=hours)
        
        # Webhook errors
        errors = WebhookLog.objects.filter(
            log_type='error',
            created_at__gte=cutoff
        ).order_by('-created_at')[:limit]
        
        if errors:
            self.stdout.write(self.style.ERROR(f'📋 {len(errors)} لاگ خطا در Webhook:'))
            for error in errors:
                self.stdout.write(f'❌ [{error.created_at.strftime("%Y-%m-%d %H:%M:%S")}] {error.title}')
                self.stdout.write(f'   {error.message[:300]}')
                if error.data:
                    self.stdout.write(f'   داده: {str(error.data)[:200]}')
                self.stdout.write('')
        else:
            self.stdout.write(self.style.SUCCESS('✅ هیچ خطایی در Webhook logs یافت نشد'))
            self.stdout.write('')
        
        # SMS errors
        if SMS_LOGS_AVAILABLE:
            sms_errors = SMSLog.objects.filter(
                status='failed',
                created_at__gte=cutoff
            ).order_by('-created_at')[:limit]
            
            if sms_errors:
                self.stdout.write(self.style.ERROR(f'📱 {len(sms_errors)} لاگ خطا در SMS:'))
                for sms_error in sms_errors:
                    self.stdout.write(f'❌ [{sms_error.created_at.strftime("%Y-%m-%d %H:%M:%S")}]')
                    self.stdout.write(f'   شماره: {sms_error.mobile_number}')
                    self.stdout.write(f'   قالب: {sms_error.template_id}')
                    self.stdout.write(f'   خطا: {sms_error.error_message or "نامشخص"}')
                    self.stdout.write('')
            else:
                self.stdout.write(self.style.SUCCESS('✅ هیچ خطایی در SMS logs یافت نشد'))






