from django.http import HttpResponse, HttpResponseRedirect
import pandas as pd
from io import BytesIO
from django.urls import path
from django.contrib import admin, messages
from .models import MiningMachine, Contractor, ContractorVehicle, MiningBlock


class MiningMachineAdmin(admin.ModelAdmin):
    list_display = ('machine_name', 'machine_type', 'ownership', 'contractor', 'is_active')
    change_list_template = "admin/mining_machine_changelist.html"

    def get_urls(self):
        """اضافه کردن مسیرهای سفارشی برای ایمپورت و دانلود فایل نمونه."""
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.admin_site.admin_view(self.import_excel_view), name='import_excel'),
            path('sample-template/', self.admin_site.admin_view(self.sample_template), name='sample_template'),
        ]
        return custom_urls + urls

    def import_excel_view(self, request):
        """پردازش فایل اکسل آپلود شده."""
        if request.method == 'POST' and 'excel_file' in request.FILES:
            excel_file = request.FILES['excel_file']
            try:
                df = pd.read_excel(excel_file)
                errors = []  # لیستی برای نگهداری خطاها

                # نگاشت مقادیر فارسی به کلیدهای انگلیسی
                machine_type_map = {
                    'بارکننده': 'Loader',
                    'حمل کننده': 'Transporter',
                    'جاده سازی': 'RoadBuilder',
                    'حفاری': 'Driller'
                }
                ownership_map = {
                    'شرکت': 'Company',
                    'پیمانکار': 'Contractor'
                }

                for index, row in df.iterrows():
                    contractor_id = None
                    if not pd.isna(row['شناسه پیمانکار']):
                        contractor_id = row['شناسه پیمانکار']
                        # بررسی وجود پیمانکار با این شناسه
                        if not Contractor.objects.filter(id=contractor_id).exists():
                            errors.append(f"ردیف {index + 1}: پیمانکاری با شناسه {contractor_id} وجود ندارد.")
                            continue

                    # تبدیل مقادیر فارسی به کلیدهای انگلیسی
                    machine_type = machine_type_map.get(row['نوع دستگاه'], None)
                    ownership = ownership_map.get(row['مالکیت'], None)

                    # بررسی صحت مقادیر نوع دستگاه
                    if not machine_type:
                        errors.append(f"ردیف {index + 1}: نوع دستگاه نامعتبر است ({row['نوع دستگاه']}).")
                        continue

                    # بررسی صحت مقادیر مالکیت
                    if not ownership:
                        errors.append(f"ردیف {index + 1}: مالکیت نامعتبر است ({row['مالکیت']}).")
                        continue

                    # تلاش برای ایجاد رکورد جدید
                    try:
                        MiningMachine.objects.create(
                            machine_type=machine_type,
                            machine_name=row['نام دستگاه'],
                            workshop_code=row['کد کارگاهی'],
                            ownership=ownership,
                            contractor_id=contractor_id,
                            is_active=row['فعال']
                        )
                    except Exception as e:
                        errors.append(f"ردیف {index + 1}: خطا در ایجاد رکورد - {e}")

                # نمایش خطاها در صورت وجود
                if errors:
                    for error in errors:
                        self.message_user(request, error, level=messages.ERROR)
                else:
                    self.message_user(request, "اطلاعات با موفقیت وارد شدند.", level=messages.SUCCESS)

                return HttpResponseRedirect("../")

            except Exception as e:
                self.message_user(request, f"خطا در پردازش فایل: {e}", level=messages.ERROR)

        return HttpResponseRedirect("../")

    def sample_template(self, request):
        """ایجاد و ارسال فایل نمونه اکسل."""
        sample_data = {
            "نوع دستگاه": ["بارکننده", "حمل کننده"],
            "نام دستگاه": ["دستگاه مثال A", "دستگاه مثال B"],
            "کد کارگاهی": ["101", "102"],
            "مالکیت": ["شرکت", "پیمانکار"],
            "شناسه پیمانکار": [None, 1],
            "فعال": [True, False],
        }
        df = pd.DataFrame(sample_data)

        # ساخت فایل اکسل در حافظه
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='نمونه')
        buffer.seek(0)

        # ارسال فایل به کاربر
        response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=نمونه_فایل_اکسل.xlsx'
        return response


admin.site.register(MiningMachine, MiningMachineAdmin)
admin.site.register(Contractor)
admin.site.register(ContractorVehicle)
admin.site.register(MiningBlock)
