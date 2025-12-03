"""
Management Command: حذف خودکار داروهای منقضی
استفاده: python manage.py cleanup_expired_medicines
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from emergency_services.models import Medicine, ExpiredMedicineLog
from dashboard.models import Notification
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    help = 'حذف خودکار داروهای منقضی، ثبت لاگ و ارسال اطلاع‌رسانی به مدیران و بازرسان'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='فقط نمایش داروهایی که حذف خواهند شد بدون حذف واقعی',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=0,
            help='حذف داروهایی که N روز پیش منقضی شده‌اند (پیش‌فرض: 0 = امروز)',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        days = options.get('days', 0)
        
        # محاسبه تاریخ برش
        cutoff_date = timezone.now().date()
        if days > 0:
            from datetime import timedelta
            cutoff_date = cutoff_date - timedelta(days=days)
        
        # یافتن داروهای منقضی
        expired_medicines = Medicine.objects.filter(expiry_date__lte=cutoff_date)
        
        if not expired_medicines.exists():
            self.stdout.write(
                self.style.SUCCESS('✓ هیچ دارویی برای حذف یافت نشد')
            )
            return
        
        expired_count = expired_medicines.count()
        self.stdout.write(
            self.style.WARNING(f'⚠️  {expired_count} دارو منقضی یافت شد')
        )
        
        # نمایش لیست داروهای منقضی
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.WARNING('لیست داروهای منقضی:'))
        self.stdout.write('='*60)
        
        medicines_list = []
        for medicine in expired_medicines:
            status = '(حذف شود)' if not dry_run else '(نمایش فقط)'
            self.stdout.write(
                f'  • {medicine.name} - تاریخ انقضا: {medicine.expiry_date} - موجودی: {medicine.quantity} {status}'
            )
            medicines_list.append({
                'name': medicine.name,
                'category': medicine.category.name if medicine.category else 'بدون دسته‌بندی',
                'expiry_date': medicine.expiry_date,
                'quantity': medicine.quantity,
            })
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('\n✓ این یک تست است - هیچ تغییری انجام نشده است')
            )
            return
        
        # دریافت مدیران و بازرسان برای ارسال اطلاع‌رسانی
        try:
            hse_group = Group.objects.get(name='مدیر HSE')
            emergency_group = Group.objects.get(name='مدیر اورژانس')
            inspector_group = Group.objects.get(name='بازرس HSE')
            
            hse_managers = User.objects.filter(groups=hse_group)
            emergency_managers = User.objects.filter(groups=emergency_group)
            inspectors = User.objects.filter(groups=inspector_group)
            
            managers = list(hse_managers) + list(emergency_managers)
            all_users = managers + list(inspectors)
        except Group.DoesNotExist:
            all_users = []
            managers = []
            self.stdout.write(
                self.style.WARNING('⚠️  گروه‌های مدیریت یافت نشدند')
            )
        
        # ثبت لاگ برای هر دارو منقضی قبل از حذف
        log_count = 0
        for medicine in expired_medicines:
            try:
                ExpiredMedicineLog.objects.create(
                    medicine_name=medicine.name,
                    medicine_category=medicine.category.name if medicine.category else 'بدون دسته‌بندی',
                    quantity=medicine.quantity,
                    expiry_date=medicine.expiry_date,
                    disposal_date=timezone.now().date(),
                    disposal_method='deleted',
                    notes=f'حذف خودکار توسط سیستم در {timezone.now()}',
                    disposal_by_user=None
                )
                log_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  خطا در ثبت لاگ برای {medicine.name}: {str(e)}')
                )
        
        # ارسال اطلاع‌رسانی درباره حذف شدن
        medicines_names = ', '.join([m['name'] for m in medicines_list[:5]])
        if expired_count > 5:
            medicines_names += f', و {expired_count - 5} دارو دیگر'
        
        for user in all_users:
            try:
                is_inspector = user.groups.filter(name='بازرس HSE').exists()
                notification_type = 'warning' if is_inspector else 'info'
                
                title = '🔴 داروهای منقضی حذف شدند' if is_inspector else 'داروهای منقضی حذف شدند'
                
                Notification.objects.create(
                    user=user,
                    title=title,
                    message=f'{expired_count} دارو منقضی حذف شدند: {medicines_names}\n\nلطفاً گزارش داروهای منقضی را بررسی کنید.',
                    notification_type=notification_type,
                    is_read=False
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  خطا در ارسال اطلاع‌رسانی به {user.username}: {str(e)}')
                )
        
        # حذف داروها
        deleted_count, _ = expired_medicines.delete()
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(f'✓ {deleted_count} دارو منقضی با موفقیت حذف شد')
        )
        self.stdout.write(
            self.style.SUCCESS(f'✓ {log_count} رکورد در گزارش داروهای منقضی ثبت شد')
        )
        
        if all_users:
            self.stdout.write(
                self.style.SUCCESS(f'✓ {len(managers)} مدیر مطلع شدند')
            )
            try:
                inspectors = User.objects.filter(groups__name='بازرس HSE')
                if inspectors.exists():
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {inspectors.count()} بازرس مطلع شدند')
                    )
            except:
                pass
        
        self.stdout.write('='*60 + '\n')
