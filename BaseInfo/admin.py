from django.http import HttpResponse, HttpResponseRedirect
import pandas as pd
from io import BytesIO
from django.urls import path
from django.contrib import admin, messages
from .models import MiningMachine, Contractor, ContractorVehicle, MiningBlock, MachineryWorkGroup, TypeMachine


class MiningMachineAdmin(admin.ModelAdmin):
    list_display = ('workshop_code', 'machine_type', 'ownership', 'is_active')
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

                for index, row in df.iterrows():
                    # بررسی وجود فیلدها در فایل اکسل
                    required_fields = ['گروه کاری', 'نوع دستگاه', 'کد کارگاهی', 'مالکیت', 'فعال']
                    for field in required_fields:
                        if field not in row or pd.isna(row[field]):
                            errors.append(f"ردیف {index + 1}: ستون '{field}' خالی است.")
                            continue

                    # مقادیر مستقیم از فایل اکسل
                    machine_workgroup_name = row['گروه کاری']
                    machine_type_name = row['نوع دستگاه']
                    ownership_name = row['مالکیت']
                    workshop_code = row['کد کارگاهی']

                    try:
                        is_active = bool(row['فعال'])
                    except ValueError:
                        errors.append(f"ردیف {index + 1}: مقدار 'فعال' باید True یا False باشد.")
                        continue

                    # بررسی یا ایجاد گروه کاری (MachineryWorkGroup)
                    workgroup, _ = MachineryWorkGroup.objects.get_or_create(
                        name=machine_workgroup_name,
                        defaults={'description': f"گروه کاری ایجاد شده در هنگام ایمپورت: {machine_workgroup_name}"}
                    )

                    # بررسی یا ایجاد نوع دستگاه (TypeMachine) مرتبط با گروه کاری
                    machine_type, _ = TypeMachine.objects.get_or_create(
                        name=machine_type_name,
                        machine_workgroup=workgroup,  # ارتباط صحیح با گروه کاری
                        defaults={'description': f"نوع دستگاه ایجاد شده در هنگام ایمپورت: {machine_type_name}"}
                    )

                    # بررسی یا ایجاد مالکیت (Contractor)
                    contractor, _ = Contractor.objects.get_or_create(
                        name=ownership_name,
                        defaults={'contact_info': f"ایجاد شده در هنگام ایمپورت: {ownership_name}"}
                    )

                    # ایجاد یا ثبت رکورد MiningMachine
                    try:
                        MiningMachine.objects.update_or_create(
                            workshop_code=workshop_code,
                            defaults={
                                'machine_workgroup': workgroup,
                                'machine_type': machine_type,
                                'ownership': contractor,
                                'is_active': is_active
                            }
                        )
                    except Exception as e:
                        errors.append(f"ردیف {index + 1}: خطا در ثبت رکورد - {str(e)}")

                # نمایش پیام خطا یا موفقیت
                if errors:
                    for error in errors:
                        self.message_user(request, error, level=messages.ERROR)
                else:
                    self.message_user(request, "تمام اطلاعات با موفقیت وارد شدند.", level=messages.SUCCESS)

                return HttpResponseRedirect("../")

            except Exception as e:
                self.message_user(request, f"خطا در پردازش فایل: {str(e)}", level=messages.ERROR)

        return HttpResponseRedirect("../")

    def sample_template(self, request):
        """ایجاد و ارسال فایل نمونه اکسل."""
        sample_data = {
            "گروه کاری": ["بارکننده", "حمل کننده"],
            "نوع دستگاه": ["Loader", "Transporter"],
            "کد کارگاهی": ["101", "102"],
            "مالکیت": ["شرکت", "پیمانکار"],
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
admin.site.register(MachineryWorkGroup)
admin.site.register(TypeMachine)
