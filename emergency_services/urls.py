from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'emergency_services'

URLS_WITH_LABELS = [
    {
        "path": "",
        "view": views.dashboard,
        "name": "dashboard",
        "label": "اورژانس_داشبورد"
    },
    {
        "path": "visits/",
        "view": views.visit_list,
        "name": "visit_list",
        "label": "اورژانس_لیست مراجعات"
    },
    {
        "path": "visits/create/",
        "view": views.create_visit,
        "name": "create_visit",
        "label": "اورژانس_ایجاد مراجعه جدید"
    },
    {
        "path": "visits/<int:pk>/",
        "view": views.visit_detail,
        "name": "visit_detail",
        "label": "اورژانس_جزئیات مراجعه"
    },
    {
        "path": "visits/<int:pk>/edit/",
        "view": views.edit_visit,
        "name": "edit_visit",
        "label": "اورژانس_ویرایش مراجعه"
    },
    {
        "path": "visits/<int:pk>/print/",
        "view": views.print_visit,
        "name": "print_visit",
        "label": "اورژانس_چاپ مراجعه"
    },
    {
        "path": "visits/export/csv/",
        "view": views.export_visits_csv,
        "name": "export_visits_csv",
        "label": "اورژانس_خروجی CSV مراجعات"
    },
    {
        "path": "services/",
        "view": views.service_list,
        "name": "service_list",
        "label": "اورژانس_لیست خدمات درمانی"
    },
    {
        "path": "services/<int:pk>/edit/",
        "view": views.edit_service,
        "name": "edit_service",
        "label": "اورژانس_ویرایش خدمات درمانی"
    },
    {
        "path": "medicines/",
        "view": views.medicine_list,
        "name": "medicine_list",
        "label": "اورژانس_لیست داروها"
    },
    {
        "path": "medicines/create/",
        "view": views.create_medicine,
        "name": "create_medicine",
        "label": "اورژانس_ایجاد داروی جدید"
    },
    {
        "path": "medicines/<int:pk>/edit/",
        "view": views.edit_medicine,
        "name": "edit_medicine",
        "label": "اورژانس_ویرایش دارو"
    },
    {
        "path": "medicines/export/csv/",
        "view": views.export_medicines_csv,
        "name": "export_medicines_csv",
        "label": "اورژانس_خروجی CSV داروها"
    },
    {
        "path": "medicines/import-excel/",
        "view": views.ImportMedicinesExcelView.as_view(),
        "name": "import_medicines_excel",
        "label": "اورژانس_ورود داروها از اکسل"
    },
    {
        "path": "medicines/download-sample/",
        "view": views.download_sample_excel,
        "name": "download_sample_excel",
        "label": "اورژانس_دانلود نمونه فایل اکسل"
    },
    {
        "path": "categories/",
        "view": views.category_list,
        "name": "category_list",
        "label": "اورژانس_لیست دسته‌بندی‌ داروها"
    },
    {
        "path": "categories/<int:pk>/edit/",
        "view": views.edit_category,
        "name": "edit_category",
        "label": "اورژانس_ویرایش دسته‌بندی دارو"
    },
    {
        "path": "visits/<int:visit_id>/add-medicine/",
        "view": views.add_medicine_to_visit,
        "name": "add_medicine_to_visit",
        "label": "اورژانس_افزودن دارو به مراجعه"
    },
    {
        "path": "medicine-usage/<int:usage_id>/remove/",
        "view": views.remove_medicine_from_visit,
        "name": "remove_medicine_from_visit",
        "label": "اورژانس_حذف دارو از مراجعه"
    },
    {
        "path": "medicine-usage/<int:usage_id>/return/",
        "view": views.return_medicine,
        "name": "return_medicine",
        "label": "اورژانس_برگشت دارو"
    },
    {
        "path": "hospitals/",
        "view": views.hospital_list,
        "name": "hospital_list",
        "label": "اورژانس_لیست بیمارستان‌ها"
    },
    {
        "path": "hospitals/create/",
        "view": views.create_hospital,
        "name": "create_hospital",
        "label": "اورژانس_ایجاد بیمارستان جدید"
    },
    {
        "path": "hospitals/<int:pk>/edit/",
        "view": views.edit_hospital,
        "name": "edit_hospital",
        "label": "اورژانس_ویرایش بیمارستان"
    },
    {
        "path": "hospitals/<int:pk>/delete/",
        "view": views.delete_hospital,
        "name": "delete_hospital",
        "label": "اورژانس_حذف بیمارستان"
    },
    {
        "path": "equipment/",
        "view": views.equipment_list,
        "name": "equipment_list",
        "label": "اورژانس_لیست تجهیزات"
    },
    {
        "path": "equipment/create/",
        "view": views.create_equipment,
        "name": "create_equipment",
        "label": "اورژانس_ایجاد تجهیز جدید"
    },
    {
        "path": "equipment/<int:pk>/edit/",
        "view": views.edit_equipment,
        "name": "edit_equipment",
        "label": "اورژانس_ویرایش تجهیز"
    },
    {
        "path": "equipment/<int:pk>/delete/",
        "view": views.delete_equipment,
        "name": "delete_equipment",
        "label": "اورژانس_حذف تجهیز"
    },
    # Reports
    {
        "path": "medicines/expired-report/",
        "view": views.expired_medicines_report,
        "name": "expired_medicines_report",
        "label": "اورژانس_گزارش داروهای منقضی"
    },
    # Data Management
    {
        "path": "data-management/",
        "view": views.data_management,
        "name": "data_management",
        "label": "اورژانس_مدیریت داده‌ها"
    },
    # API Endpoints
    {
        "path": "api/medicines/",
        "view": views.api_medicines_list,
        "name": "api_medicines_list",
        "label": "اورژانس_API لیست داروها"
    },
    {
        "path": "api/medicines/save/",
        "view": views.api_medicine_save,
        "name": "api_medicine_save",
        "label": "اورژانس_API ذخیره دارو"
    },
    {
        "path": "api/medicines/<int:pk>/delete/",
        "view": views.api_medicine_delete,
        "name": "api_medicine_delete",
        "label": "اورژانس_API حذف دارو"
    },
    {
        "path": "api/medicines/<int:pk>/increase-stock/",
        "view": views.api_medicine_increase_stock,
        "name": "api_medicine_increase_stock",
        "label": "اورژانس_API افزایش موجودی دارو"
    },
    {
        "path": "api/categories/",
        "view": views.api_categories_list,
        "name": "api_categories_list",
        "label": "اورژانس_API لیست دسته‌بندی‌ها"
    },
    {
        "path": "api/categories/save/",
        "view": views.api_category_save,
        "name": "api_category_save",
        "label": "اورژانس_API ذخیره دسته‌بندی"
    },
    {
        "path": "api/categories/<int:pk>/delete/",
        "view": views.api_category_delete,
        "name": "api_category_delete",
        "label": "اورژانس_API حذف دسته‌بندی"
    },
    {
        "path": "api/services/",
        "view": views.api_services_list,
        "name": "api_services_list",
        "label": "اورژانس_API لیست خدمات"
    },
    {
        "path": "api/services/save/",
        "view": views.api_service_save,
        "name": "api_service_save",
        "label": "اورژانس_API ذخیره خدمت"
    },
    {
        "path": "api/services/<int:pk>/delete/",
        "view": views.api_service_delete,
        "name": "api_service_delete",
        "label": "اورژانس_API حذف خدمت"
    },
    {
        "path": "api/equipment/",
        "view": views.api_equipment_list,
        "name": "api_equipment_list",
        "label": "اورژانس_API لیست تجهیزات"
    },
    {
        "path": "api/equipment/save/",
        "view": views.api_equipment_save,
        "name": "api_equipment_save",
        "label": "اورژانس_API ذخیره تجهیز"
    },
    {
        "path": "api/equipment/<int:pk>/delete/",
        "view": views.api_equipment_delete,
        "name": "api_equipment_delete",
        "label": "اورژانس_API حذف تجهیز"
    },
    {
        "path": "api/hospitals/",
        "view": views.api_hospitals_list,
        "name": "api_hospitals_list",
        "label": "اورژانس_API لیست بیمارستان‌ها"
    },
    {
        "path": "api/hospitals/save/",
        "view": views.api_hospital_save,
        "name": "api_hospital_save",
        "label": "اورژانس_API ذخیره بیمارستان"
    },
    {
        "path": "api/hospitals/<int:pk>/delete/",
        "view": views.api_hospital_delete,
        "name": "api_hospital_delete",
        "label": "اورژانس_API حذف بیمارستان"
    },
    {
        "path": "api/personnel/",
        "view": views.api_personnel_list,
        "name": "api_personnel_list",
        "label": "اورژانس_API لیست پرسنل"
    },
    {
        "path": "api/personnel/save/",
        "view": views.api_personnel_save,
        "name": "api_personnel_save",
        "label": "اورژانس_API ذخیره پرسنل"
    },
    {
        "path": "api/personnel/<int:pk>/delete/",
        "view": views.api_personnel_delete,
        "name": "api_personnel_delete",
        "label": "اورژانس_API حذف پرسنل"
    },
    {
        "path": "api/personnel/<int:pk>/",
        "view": views.api_personnel_detail,
        "name": "api_personnel_detail",
        "label": "اورژانس_API جزئیات پرسنل"
    },
    # Emergency Portal Login/Logout
    {
        "path": "login/",
        "view": views.emergency_login_view,
        "name": "emergency_login",
        "label": "اورژانس_ورود پرسنل"
    },
    {
        "path": "logout/",
        "view": views.emergency_logout_view,
        "name": "emergency_logout",
        "label": "اورژانس_خروج پرسنل"
    },
    # Emergency Password Reset
    {
        "path": "password-reset/",
        "view": views.emergency_password_reset_view,
        "name": "emergency_password_reset",
        "label": "اورژانس_بازیابی رمز عبور"
    },
    {
        "path": "password-reset/done/",
        "view": views.emergency_password_reset_done_view,
        "name": "emergency_password_reset_done",
        "label": "اورژانس_تایید بازیابی رمز عبور"
    },
    {
        "path": "password-reset-confirm/<uidb64>/<token>/",
        "view": auth_views.PasswordResetConfirmView.as_view(
            template_name='emergency_services/emergency_password_reset_confirm.html',
            success_url='/emergency/password-reset-complete/'
        ),
        "name": "emergency_password_reset_confirm",
        "label": "اورژانس_تایید رمز عبور جدید"
    },
    {
        "path": "password-reset-complete/",
        "view": auth_views.PasswordResetCompleteView.as_view(
            template_name='emergency_services/emergency_password_reset_complete.html'
        ),
        "name": "emergency_password_reset_complete",
        "label": "اورژانس_تکمیل بازیابی رمز عبور"
    },
    # Emergency Profile
    {
        "path": "profile/",
        "view": views.emergency_profile,
        "name": "emergency_profile",
        "label": "اورژانس_پروفایل پرسنل"
    },
    {
        "path": "profile/change-password/",
        "view": views.emergency_change_password,
        "name": "emergency_change_password",
        "label": "اورژانس_تغییر رمز عبور"
    }
]

urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
]
