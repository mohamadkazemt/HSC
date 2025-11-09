"""
Django management command to find and fix duplicate UserProfiles.

Usage:
    python manage.py fix_duplicate_profiles --list  # List duplicates
    python manage.py fix_duplicate_profiles --fix   # Fix duplicates
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Find and fix duplicate UserProfiles with the same personnel_code'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='List duplicate profiles',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix duplicate profiles by keeping the first one',
        )

    def handle(self, *args, **options):
        # Find personnel codes that have multiple profiles
        duplicates = (
            UserProfile.objects
            .values('personnel_code')
            .annotate(count=Count('id'))
            .filter(count__gt=1, personnel_code__isnull=False)
            .exclude(personnel_code='')
        )

        if not duplicates:
            self.stdout.write(self.style.SUCCESS('✅ هیچ پروفایل تکراری یافت نشد!'))
            return

        self.stdout.write(
            self.style.WARNING(
                f'⚠️ تعداد {len(duplicates)} کد پرسنلی با پروفایل‌های تکراری یافت شد:'
            )
        )

        for dup in duplicates:
            personnel_code = dup['personnel_code']
            count = dup['count']
            
            profiles = UserProfile.objects.filter(personnel_code=personnel_code).order_by('id')
            
            self.stdout.write(f'\n📋 کد پرسنلی: {personnel_code} ({count} پروفایل)')
            
            for i, profile in enumerate(profiles, 1):
                user_info = f'{profile.user.username} ({profile.user.get_full_name()})' if profile.user else 'بدون کاربر'
                payslips_count = profile.payslips.count() if hasattr(profile, 'payslips') else 0
                
                marker = '✓ (نگه داشته می‌شود)' if i == 1 else '✗ (حذف می‌شود)'
                
                self.stdout.write(
                    f'  {i}. ID={profile.id}, User={user_info}, '
                    f'Payslips={payslips_count} {marker if options["fix"] else ""}'
                )

            if options['fix']:
                # Keep the first profile, delete others
                first_profile = profiles.first()
                duplicates_to_delete = profiles.exclude(id=first_profile.id)
                
                # Transfer payslips if any
                for dup_profile in duplicates_to_delete:
                    if hasattr(dup_profile, 'payslips'):
                        payslips = dup_profile.payslips.all()
                        if payslips.exists():
                            self.stdout.write(
                                self.style.WARNING(
                                    f'    ⚠️ انتقال {payslips.count()} فیش حقوقی از پروفایل {dup_profile.id} به {first_profile.id}'
                                )
                            )
                            for payslip in payslips:
                                # Check if payslip already exists for this month/year
                                existing = first_profile.payslips.filter(
                                    year=payslip.year,
                                    month=payslip.month
                                ).first()
                                
                                if existing:
                                    self.stdout.write(
                                        f'      ⚠️ فیش {payslip.year}/{payslip.month} قبلاً وجود دارد، حذف نسخه تکراری'
                                    )
                                    payslip.delete()
                                else:
                                    payslip.user_profile = first_profile
                                    payslip.save()
                
                # Delete duplicate profiles
                deleted_count = duplicates_to_delete.count()
                duplicates_to_delete.delete()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✅ {deleted_count} پروفایل تکراری حذف شد'
                    )
                )

        if options['fix']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ تمیزسازی کامل شد! {len(duplicates)} کد پرسنلی اصلاح شد.'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️ برای اصلاح مشکلات، دستور را با پارامتر --fix اجرا کنید:'
                )
            )
            self.stdout.write('    python manage.py fix_duplicate_profiles --fix')

