from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import UserProfile
from django.contrib.auth.models import User
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget


class UserProfileResource(resources.ModelResource):
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, 'username')
    )

    class Meta:
        model = UserProfile
        import_id_fields = ['personnel_code']
        fields = ('personnel_code', 'mobile', 'group', 'user')
        export_order = fields

    def before_import_row(self, row, **kwargs):
        personnel_code = str(row.get('personnel_code', '')).strip()
        mobile = str(row.get('mobile', '')).strip()

        # اگر کاربر با این کد پرسنلی وجود نداشت، یک کاربر جدید بسازید
        try:
            User.objects.get(username=personnel_code)
        except User.DoesNotExist:
            user = User.objects.create(
                username=personnel_code,
                first_name=row.get('first_name', ''),
                last_name=row.get('last_name', '')
            )
            # تنظیم شماره موبایل به عنوان رمز عبور
            user.set_password(mobile)
            user.save()
            row['user'] = user.username


@admin.register(UserProfile)
class UserProfileAdmin(ImportExportModelAdmin):
    resource_class = UserProfileResource
    list_display = ('personnel_code', 'user', 'group', 'mobile')
    search_fields = ('personnel_code', 'user__username', 'group', 'mobile')
    list_filter = ('group',)