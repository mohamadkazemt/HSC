"""
Management command to fix night shift reports that were incorrectly calculated.

This command corrects DailyReport records that were created during night shifts
(22:45 to 6:45) by recalculating the correct shift based on the proper date.

Usage:
    python manage.py fix_night_shift_reports
    python manage.py fix_night_shift_reports --dry-run  # Preview changes without saving
    python manage.py fix_night_shift_reports --verbose   # Show detailed output
"""
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from dailyreport_hse.models import DailyReport
from shift_manager.utils import get_shift_for_date
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Fix night shift reports that were incorrectly calculated'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without actually updating the database',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each report',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('شروع اصلاح گزارش‌های شب کاری...'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('حالت پیش‌نمایش فعال است - هیچ تغییری ذخیره نخواهد شد'))
        
        # Find all reports that were created during night shift hours
        # Night shift: 22:45 to 6:45 (next day)
        all_reports = DailyReport.objects.all().select_related('user', 'user__userprofile')
        
        fixed_count = 0
        skipped_count = 0
        error_count = 0
        
        with transaction.atomic():
            for report in all_reports:
                try:
                    # Get the creation time
                    created_time = report.created_at.time()
                    created_date = report.created_at.date()
                    
                    # Check if this report was created during night shift hours
                    is_night_shift_time = (
                        created_time >= datetime.time(22, 45) or 
                        created_time < datetime.time(6, 45)
                    )
                    
                    if not is_night_shift_time:
                        # Not a night shift report, skip it
                        skipped_count += 1
                        if verbose:
                            self.stdout.write(
                                f'رد شد: گزارش #{report.id} - زمان: {created_time} (شیفت شب نیست)'
                            )
                        continue
                    
                    # Determine the correct date for shift calculation
                    # If time is between 00:00 and 6:45, use previous day
                    # If time is between 22:45 and 23:59, use current day
                    if created_time < datetime.time(6, 45):
                        # Between 00:00 and 6:45, use previous day
                        correct_date = created_date - datetime.timedelta(days=1)
                    else:
                        # Between 22:45 and 23:59, use current day
                        correct_date = created_date
                    
                    # Get user profile to determine the correct shift
                    user_profile = None
                    if hasattr(report.user, 'userprofile'):
                        user_profile = report.user.userprofile
                    
                    if not user_profile or not user_profile.group:
                        self.stdout.write(
                            self.style.WARNING(
                                f'خطا: گزارش #{report.id} - کاربر {report.user.username} '
                                f'گروه کاری ندارد'
                            )
                        )
                        error_count += 1
                        continue
                    
                    # Calculate the correct shift for the correct date
                    shifts = get_shift_for_date(correct_date, user_profile)
                    correct_shift = shifts.get('user_group_shift')
                    correct_group = shifts.get('user_group')
                    
                    if not correct_shift:
                        self.stdout.write(
                            self.style.WARNING(
                                f'خطا: گزارش #{report.id} - نتوانست شیفت صحیح را محاسبه کند'
                            )
                        )
                        error_count += 1
                        continue
                    
                    # Check if shift or group needs to be updated
                    needs_update = False
                    changes = []
                    
                    if report.shift != correct_shift:
                        needs_update = True
                        changes.append(f'شیفت: {report.shift} → {correct_shift}')
                    
                    if report.work_group != correct_group:
                        needs_update = True
                        changes.append(f'گروه: {report.work_group} → {correct_group}')
                    
                    if needs_update:
                        if verbose:
                            self.stdout.write(
                                f'اصلاح: گزارش #{report.id} - کاربر: {report.user.username} - '
                                f'تاریخ ثبت: {created_date} {created_time} - '
                                f'تاریخ صحیح: {correct_date} - '
                                f'تغییرات: {", ".join(changes)}'
                            )
                        
                        if not dry_run:
                            report.shift = correct_shift
                            report.work_group = correct_group
                            report.save(update_fields=['shift', 'work_group'])
                        
                        fixed_count += 1
                    else:
                        skipped_count += 1
                        if verbose:
                            self.stdout.write(
                                f'بدون تغییر: گزارش #{report.id} - '
                                f'شیفت و گروه صحیح است'
                            )
                
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'خطا در پردازش گزارش #{report.id}: {str(e)}'
                        )
                    )
                    error_count += 1
            
            if dry_run:
                # Rollback transaction in dry-run mode
                transaction.set_rollback(True)
        
        # Print summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('خلاصه نتایج:'))
        self.stdout.write(f'  گزارش‌های اصلاح شده: {fixed_count}')
        self.stdout.write(f'  گزارش‌های بدون تغییر: {skipped_count}')
        self.stdout.write(f'  خطاها: {error_count}')
        self.stdout.write(f'  کل گزارش‌ها: {all_reports.count()}')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\nاین یک پیش‌نمایش بود. برای اعمال تغییرات، دستور را بدون --dry-run اجرا کنید.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('\nاصلاح گزارش‌ها با موفقیت انجام شد!'))

