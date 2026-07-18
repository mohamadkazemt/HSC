from django.http import HttpResponse, HttpResponseRedirect
import pandas as pd
from io import BytesIO
from django.urls import path
from django.contrib import admin, messages
from .models import UserProfile, Section, Part, Position, UnitGroup, DriverLicense
from .personnel_excel import import_personnel_dataframe, sample_dataframe

class UserImportAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'first_name',
        'last_name',
        'personnel_code',
        'national_id',
        'unit',
        'position',
        'unit_group',
        'part',
        'section',
        'group',
        'mobile',
    )

    list_filter = ('section', 'part', 'unit_group', 'position','group')

    search_fields = ('user__username', 'personnel_code', 'mobile', 'user__first_name', 'user__last_name')

    change_list_template = "admin/user_import_changelist.html"

    def first_name(self, obj):
        return obj.user.first_name
    first_name.short_description = "نام"

    def last_name(self, obj):
        return obj.user.last_name
    last_name.short_description = "نام خانوادگی"

    def national_id(self, obj):
        return obj.user.username
    national_id.short_description = "کد ملی"

    def get_urls(self):
        """اضافه کردن مسیرهای سفارشی برای ایمپورت و دانلود فایل نمونه."""
        urls = super().get_urls()
        custom_urls = [
            path('import-users/', self.admin_site.admin_view(self.import_users_view), name='import_users'),
            path('sample-user-template/', self.admin_site.admin_view(self.sample_user_template), name='sample_user_template'),
        ]
        return custom_urls + urls

    def import_users_view(self, request):
        if request.method == 'POST' and 'excel_file' in request.FILES:
            try:
                df = pd.read_excel(request.FILES['excel_file'])
                created_count, updated_count, errors, missing_columns = import_personnel_dataframe(df)
                if missing_columns:
                    self.message_user(
                        request,
                        f"فایل بارگذاری شده دارای ستون‌های ناقص است: {', '.join(missing_columns)}",
                        level=messages.ERROR
                    )
                    return HttpResponseRedirect("../")
                for error in errors:
                    self.message_user(request, error, level=messages.ERROR)
                if created_count or updated_count:
                    self.message_user(
                        request,
                        f'{created_count} پرسنل ایجاد و {updated_count} پرسنل به‌روزرسانی شد.',
                        level=messages.SUCCESS,
                    )

            except Exception as e:
                self.message_user(request, f"خطا در پردازش فایل: {str(e)}", level=messages.ERROR)

        return HttpResponseRedirect("../")

    def sample_user_template(self, request):
        df = sample_dataframe()

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='نمونه')
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=نمونه_کاربران.xlsx'
        return response


admin.site.register(UserProfile, UserImportAdmin)

@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
@admin.register(UnitGroup)
class UnitGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')

@admin.register(DriverLicense)
class DriverLicenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_base', 'expiry_date', 'has_special', 'is_verified')
    list_filter = ('license_base', 'has_special', 'is_verified')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user',)
        }),
        ('اطلاعات گواهینامه', {
            'fields': ('license_base', 'expiry_date', 'has_special', 'special_codes')
        }),
        ('تصاویر', {
            'fields': ('front_image', 'back_image')
        }),
        ('وضعیت', {
            'fields': ('is_verified',)
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
