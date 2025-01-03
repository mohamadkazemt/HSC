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
    list_display = (
        'user',
        'first_name',
        'last_name',
        'personnel_code',
        'national_id',
        'position',
        'unit',
        'department',
        'mobile',
        'group',
    )

    list_filter = ('department', 'unit', 'group', 'position')

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
            excel_file = request.FILES['excel_file']
            try:
                df = pd.read_excel(excel_file)
                errors = []

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
                        # استانداردسازی مقادیر
                        mobile = str(row['موبایل']).strip()
                        if not mobile.startswith('0'):
                            mobile = '0' + mobile

                        department_name = str(row['واحد']).strip().lower()
                        unit_name = str(row['بخش']).strip().lower()
                        position_name = str(row['سمت']).strip().lower()
                        personnel_code = str(row['کد پرسنلی']).strip()
                        national_id = str(row['کد ملی']).strip()
                        first_name = str(row['نام']).strip()
                        last_name = str(row['نام خانوادگی']).strip()

                        # جلوگیری از ایجاد واحد تکراری
                        department, _ = Department.objects.get_or_create(
                            name=department_name
                        )

                        # جلوگیری از ایجاد بخش تکراری
                        unit, _ = Unit.objects.get_or_create(
                            name=unit_name,
                            department=department
                        )

                        # جلوگیری از ایجاد سمت تکراری
                        position, _ = Position.objects.get_or_create(
                            name=position_name,
                            unit=unit
                        )

                        # بررسی تکراری بودن کد پرسنلی
                        user_profile = UserProfile.objects.filter(personnel_code=personnel_code).first()
                        if user_profile:
                            updates = []
                            if user_profile.user.first_name != first_name:
                                user_profile.user.first_name = first_name
                                updates.append("نام")
                            if user_profile.user.last_name != last_name:
                                user_profile.user.last_name = last_name
                                updates.append("نام خانوادگی")
                            if user_profile.mobile != mobile:
                                user_profile.mobile = mobile
                                updates.append("شماره موبایل")
                            if user_profile.department != department:
                                user_profile.department = department
                                updates.append("واحد")
                            if user_profile.unit != unit:
                                user_profile.unit = unit
                                updates.append("بخش")
                            if user_profile.position != position:
                                user_profile.position = position
                                updates.append("سمت")
                            if updates:
                                user_profile.user.save()
                                user_profile.save()
                                errors.append(f"ردیف {index + 1}: اطلاعات زیر به‌روزرسانی شد: {', '.join(updates)}")
                            continue

                        # ایجاد کاربر جدید در صورت عدم وجود
                        user, created = User.objects.update_or_create(
                            username=national_id,
                            defaults={
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': f"{national_id}@example.com",
                            }
                        )
                        if created:
                            random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                            user.set_password(random_password)
                            user.save()

                        # ایجاد پروفایل کاربر
                        UserProfile.objects.create(
                            user=user,
                            personnel_code=personnel_code,
                            mobile=mobile,
                            group=str(row['گروه کاری']).strip(),
                            department=department,
                            unit=unit,
                            position=position
                        )
                    except Exception as e:
                        errors.append(f"ردیف {index + 1}: خطا در ذخیره‌سازی کاربر - {str(e)}")

                if errors:
                    for error in errors:
                        self.message_user(request, error, level=messages.ERROR)
                else:
                    self.message_user(request, "کاربران با موفقیت وارد شدند.", level=messages.SUCCESS)

            except Exception as e:
                self.message_user(request, f"خطا در پردازش فایل: {str(e)}", level=messages.ERROR)

        return HttpResponseRedirect("../")

    def sample_user_template(self, request):
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
