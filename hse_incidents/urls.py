from django.urls import path
from . import views

app_name = 'hse_incidents'

URLS_WITH_LABELS = [
    {
        "path": "incident_report/",
        "view": views.report_incident,
        "name": "incident_report",
        "label": "حوادث HSE_گزارش حادثه",
    },
    {
        "path": "get_injury_types_ajax/",
        "view": views.get_injury_types_ajax,
        "name": "get_injury_types_ajax",
        "label": "حوادث HSE_دریافت انواع آسیب (آژاکس)",
    },
    {
        "path": "get_contractors_ajax/",
        "view": views.get_contractors_ajax,
        "name": "get_contractors_ajax",
        "label": "حوادث HSE_دریافت پیمانکاران (آژاکس)",
    },
    {
        "path": "get_contractor_employees_ajax/",
        "view": views.get_contractor_employees_ajax,
        "name": "get_contractor_employees_ajax",
        "label": "حوادث HSE_دریافت پرسنل پیمانکار (آژاکس)",
    },
    {
        "path": "get_user_profiles_ajax/",
        "view": views.get_user_profiles_ajax,
        "name": "get_user_profiles_ajax",
        "label": "حوادث HSE_دریافت لیست کاربران (آژاکس)",
    },
    {
        "path": "list_reports/",
        "view": views.list_reports,
        "name": "list_reports",
        "label": "حوادث HSE_لیست گزارش‌ها",
    },
     {
        "path": "report_details/<int:report_id>/",
        "view": views.report_details,
        "name": "report_details",
        "label": "حوادث HSE_جزئیات گزارش",
    },
    {
        "path": "export_reports_excel/",
        "view": views.export_reports_excel,
        "name": "export_reports_excel",
        "label": "حوادث HSE_خروجی اکسل گزارش‌ها",
    },
    {
        "path": "report_details_pdf/<int:report_id>/",
        "view": views.report_details_pdf,
        "name": "report_details_pdf",
        "label": "حوادث HSE_دریافت PDF گزارش",
    },
    {
        "path": "submit_completion/<int:report_id>/",
        "view": views.submit_hse_completion_ajax,
        "name": "submit_completion",
        "label": "حوادث HSE_ارسال فرم تکمیل (AJAX)",
    },
    {
        "path": "injury_types/",
        "view": views.injury_types_list,
        "name": "injury_types_list",
        "label": "مدیریت جراحات_لیست انواع جراحت",
    },
    {
        "path": "injury_types/create/",
        "view": views.injury_type_create_ajax,
        "name": "injury_type_create",
        "label": "مدیریت جراحات_ایجاد جراحت جدید (AJAX)",
    },
    {
        "path": "injury_types/update/<int:pk>/",
        "view": views.injury_type_update_ajax,
        "name": "injury_type_update",
        "label": "مدیریت جراحات_ویرایش جراحت (AJAX)",
    },
    {
        "path": "injury_types/delete/<int:pk>/",
        "view": views.injury_type_delete_ajax,
        "name": "injury_type_delete",
        "label": "مدیریت جراحات_حذف جراحت (AJAX)",
    },
    {
        "path": "dashboard/",
        "view": views.incident_dashboard,
        "name": "dashboard",
        "label": "حوادث HSE_داشبورد حوادث",
    },
    {
        "path": "dashboard/update_start_date/",
        "view": views.update_dashboard_start_date_ajax,
        "name": "update_dashboard_start_date",
        "label": "حوادث HSE_به‌روزرسانی تاریخ شروع (AJAX)",
    },
    {
        "path": "import/template/",
        "view": views.download_import_template,
        "name": "download_import_template",
        "label": "حوادث HSE_دانلود الگوی ایمپورت اکسل",
    },
    {
        "path": "import/upload/",
        "view": views.import_incidents_from_excel,
        "name": "import_incidents",
        "label": "حوادث HSE_ایمپورت حوادث از اکسل",
    },
]

urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
]
