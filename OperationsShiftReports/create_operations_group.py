from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from OperationsShiftReports.models import ShiftReport, LoadingOperation, ShiftLeave, VehicleReport, LoaderStatus


class Command(BaseCommand):
    help = 'Creates operations group and assigns permissions'

    def handle(self, *args, **options):
        # ایجاد گروه عملیات اگر وجود نداشته باشد
        operations_group, created = Group.objects.get_or_create(name='operations')

        if created:
            self.stdout.write(self.style.SUCCESS('گروه عملیات با موفقیت ایجاد شد.'))
        else:
            self.stdout.write(self.style.WARNING('گروه عملیات قبلاً وجود داشته است.'))

        # لیست مدل‌هایی که گروه عملیات باید به آنها دسترسی داشته باشد
        models = [ShiftReport, LoadingOperation, ShiftLeave, VehicleReport, LoaderStatus]

        # اضافه کردن تمام مجوزهای مربوط به مدل‌ها
        for model in models:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=content_type)

            for permission in permissions:
                operations_group.permissions.add(permission)
                self.stdout.write(f'مجوز {permission.codename} برای {model.__name__} اضافه شد.')

        self.stdout.write(self.style.SUCCESS('تمام مجوزها با موفقیت اضافه شدند.'))