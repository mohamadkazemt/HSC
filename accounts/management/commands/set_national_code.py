from django.core.management.base import BaseCommand
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'تنظیم کد ملی برای یک کاربر'

    def add_arguments(self, parser):
        parser.add_argument('personnel_code', type=str, help='کد پرسنلی کاربر')
        parser.add_argument('national_code', type=str, help='کد ملی 10 رقمی')

    def handle(self, *args, **options):
        personnel_code = options['personnel_code']
        national_code = options['national_code']

        try:
            profile = UserProfile.objects.get(personnel_code=personnel_code)
            profile.national_code = national_code
            profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ کد ملی {national_code} برای کاربر {profile.user.get_full_name()} '
                    f'(کد پرسنلی: {personnel_code}) ثبت شد.'
                )
            )
            self.stdout.write(f'   نام کاربری: {profile.user.username}')
            self.stdout.write(f'   موبایل: {profile.mobile or "خالی"}')
            
        except UserProfile.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ کاربری با کد پرسنلی {personnel_code} یافت نشد.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ خطا: {e}')
            )
