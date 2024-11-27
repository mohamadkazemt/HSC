import random
import string
from django.http import HttpResponse, HttpResponseRedirect
import pandas as pd
from io import BytesIO
from django.urls import path
from django.contrib import admin, messages
from django.contrib.auth.models import User
from .models import UserProfile, Department, Unit, Position


class UserImportAdmin(admin.ModelAdmin):
    # نمایش ستون‌ها در جدول ادمین
    list_display = (
        'user',             # نام کاربری
        'first_name',       # نام
        'last_name',        # نام خانوادگی
        'personnel_code',   # کد پرسنلی
        'national_id',      # کد ملی
        'position',         # سمت
        'unit',             # واحد
        'department',       # بخش
        'mobile',           # موبایل
        'group',            # گروه کاری
    )

    # فیلترهای سمت راست پنل
    list_filter = (
        'department',  # فیلتر بر اساس واحد
        'unit',    # فیلتر بر اساس بخش
        'group',   # فیلتر بر اساس گروه کاری
        'position' # فیلتر بر اساس سمت
    )

    # قابلیت جستجو بر اساس برخی فیلدها
    search_fields = ('user__username', 'personnel_code', 'mobile', 'user__first_name', 'user__last_name')

    # نام‌گذاری فیلدها برای نمایش بهتر
    def first_name(self, obj):
        return obj.user.first_name
    first_name.short_description = "نام"

    def last_name(self, obj):
        return obj.user.last_name
    last_name.short_description = "نام خانوادگی"

    def national_id(self, obj):
        return obj.user.username
    national_id.short_description = "کد ملی"

    def mobile(self, obj):
        return obj.user.username
    change_list_template = "admin/user_import_changelist.html"

    def get_urls(self):
        """اضافه کردن مسیرهای سفارشی برای ایمپورت و دانلود فایل نمونه."""
        urls = super().get_urls()
        custom_urls = [
            path('import-users/', self.admin_site.admin_view(self.import_users_view), name='import_users'),
            path('sample-user-template/', self.admin_site.admin_view(self.sample_user_template), name='sample_user_template'),
        ]
        return custom_urls + urls

    def import_users_view(self, request):
        """پردازش فایل اکسل کاربران آپلود شده."""
        if request.method == 'POST' and 'excel_file' in request.FILES:
            excel_file = request.FILES['excel_file']
            try:
                df = pd.read_excel(excel_file)
                errors = []  # لیستی برای نگهداری خطاها

                # بررسی ستون‌های ضروری
                required_columns = [
                    'کد پرسنلی', 'نام', 'نام خانوادگی', 'واحد', 'بخش',
                    'سمت', 'موبایل', 'کد ملی', 'گروه کاری'
                ]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    self.message_user(
                        request,
                        f"فایل بارگذاری شده دارای ستون‌های ناقص است: {', '.join(missing_columns)}",
                        level=messages.ERROR
                    )
                    return HttpResponseRedirect("../")

                for index, row in df.iterrows():
                    try:
                        # ایجاد یا بررسی واحد (Department)
                        department, _ = Department.objects.get_or_create(
                            name=row['واحد'],
                            defaults={'description': f"واحد ایجاد شده در ایمپورت: {row['واحد']}"}
                        )

                        # ایجاد یا بررسی بخش (Unit) مرتبط با واحد
                        unit, _ = Unit.objects.get_or_create(
                            name=row['بخش'],
                            department=department,  # ارتباط صحیح با واحد
                            defaults={'description': f"بخش ایجاد شده در ایمپورت: {row['بخش']}"}
                        )

                        # ایجاد یا بررسی سمت (Position) مرتبط با بخش
                        position, _ = Position.objects.get_or_create(
                            name=row['سمت'],
                            unit=unit,  # ارتباط صحیح با بخش
                            defaults={'description': f"سمت ایجاد شده در ایمپورت: {row['سمت']}"}
                        )

                        # تولید رمز عبور تصادفی
                        random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                        # ایجاد یا به‌روزرسانی کاربر
                        user, created = User.objects.update_or_create(
                            username=row['کد ملی'],  # کد ملی به عنوان نام کاربری
                            defaults={
                                'first_name': row['نام'],
                                'last_name': row['نام خانوادگی'],
                                'email': f"{row['کد ملی']}@example.com",  # ایمیل فرضی
                            }
                        )
                        if created:
                            user.set_password(random_password)
                            user.save()

                        # ایجاد یا به‌روزرسانی پروفایل کاربر
                        UserProfile.objects.update_or_create(
                            user=user,
                            defaults={
                                'personnel_code': row['کد پرسنلی'],
                                'mobile': row['موبایل'],
                                'group': row['گروه کاری'],
                                'department': department,  # واحد مرتبط
                                'unit': unit,  # بخش مرتبط
                                'position': position  # سمت مرتبط
                            }
                        )

                    except Exception as e:
                        errors.append(f"ردیف {index + 1}: خطا در ذخیره‌سازی کاربر - {str(e)}")

                # نمایش پیام خطا یا موفقیت
                if errors:
                    for error in errors:
                        self.message_user(request, error, level=messages.ERROR)
                else:
                    self.message_user(request, "کاربران با موفقیت وارد شدند.", level=messages.SUCCESS)

            except Exception as e:
                self.message_user(request, f"خطا در پردازش فایل: {str(e)}", level=messages.ERROR)

        return HttpResponseRedirect("../")

    def sample_user_template(self, request):
        """ایجاد و ارسال فایل نمونه اکسل برای کاربران."""
        sample_data = {
            "کد پرسنلی": ["12345", "67890"],
            "نام": ["علی", "زهرا"],
            "نام خانوادگی": ["رضایی", "کاظمی"],
            "واحد": ["واحد 1", "واحد 2"],
            "بخش": ["بخش 1", "بخش 2"],
            "سمت": ["مدیر", "کارمند"],
            "موبایل": ["09123456789", "09387654321"],
            "کد ملی": ["1111111111", "2222222222"],
            "گروه کاری": ["A", "B"],
        }
        df = pd.DataFrame(sample_data)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='نمونه')
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=نمونه_کاربران.xlsx'
        return response


admin.site.register(UserProfile, UserImportAdmin)



@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
