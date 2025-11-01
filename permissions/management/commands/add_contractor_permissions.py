from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from permissions.models import UserPermission


class Command(BaseCommand):
    help = 'اضافه کردن دسترسی مدیریت پیمانکاران به کاربر'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='نام کاربری')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'کاربر "{username}" یافت نشد'))
            return

        # لیست view های مربوط به مدیریت پیمانکاران
        contractor_views = [
            'contractor_dashboard',
            'data_management',
            'contractor_create',
            'contractor_edit',
            'contractor_delete',
            'employee_create',
            'employee_edit',
            'employee_delete',
            'vehicle_create',
            'vehicle_edit',
            'vehicle_delete',
        ]

        created_count = 0
        updated_count = 0

        for view_name in contractor_views:
            permission, created = UserPermission.objects.get_or_create(
                user=user,
                view_name=view_name,
                defaults={
                    'can_view': True,
                    'can_add': True,
                    'can_edit': True,
                    'can_delete': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ دسترسی "{view_name}" ایجاد شد'))
            else:
                # اگر قبلاً وجود داشت، آن را به‌روزرسانی کن
                permission.can_view = True
                permission.can_add = True
                permission.can_edit = True
                permission.can_delete = True
                permission.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'↻ دسترسی "{view_name}" به‌روزرسانی شد'))

        self.stdout.write(self.style.SUCCESS(f'\n✓ کامل شد!'))
        self.stdout.write(self.style.SUCCESS(f'  • {created_count} دسترسی جدید ایجاد شد'))
        self.stdout.write(self.style.SUCCESS(f'  • {updated_count} دسترسی به‌روزرسانی شد'))
        self.stdout.write(self.style.SUCCESS(f'\nکاربر "{username}" اکنون به تمام بخش‌های مدیریت پیمانکاران دسترسی دارد.'))
