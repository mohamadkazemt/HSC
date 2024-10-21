from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import UserProfile
from django.contrib.auth.models import User
from import_export import resources


# تعریف resource برای UserProfile
class UserProfileResource(resources.ModelResource):
    class Meta:
        model = UserProfile

    # override کردن متد before_save_instance برای تنظیم نام کاربری و رمز عبور
    def before_save_instance(self, instance, using_transactions, dry_run):
        # بررسی اینکه User وجود دارد یا نه
        if not instance.user:
            # ایجاد کاربر جدید
            username = f"user_{instance.mobile}"

            # بررسی اینکه نام کاربری یکتا باشد
            if User.objects.filter(username=username).exists():
                raise ValueError(f"Username {username} already exists. Please provide unique mobile.")

            user = User.objects.create(
                username=username,
                first_name=instance.user.first_name if instance.user else "",
                last_name=instance.user.last_name if instance.user else "",
            )
            user.set_password('default_password')  # تنظیم رمز عبور پیش‌فرض
            user.save()

            # اتصال User به UserProfile
            instance.user = user


# تعریف admin با استفاده از UserProfileResource
@admin.register(UserProfile)
class UserProfileAdmin(ImportExportModelAdmin):
    resource_class = UserProfileResource
    list_display = ('user', 'group', 'mobile')
    search_fields = ('user__username', 'group', 'mobile')
