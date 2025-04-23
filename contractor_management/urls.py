from django.urls import path
from . import views

app_name = 'contractor_management'

URLS_WITH_LABELS = [
    {
        "path": "create-report/",
        "view": views.create_report,
        "name": "create_report",
        "label": "پیمانکاران-ایجاد گزارش کارکرد خودروها",
    },
    {
        "path": "reports/",
        "view": views.all_reports,
        "name": "all_reports",
        "label": "پیمانکاران-گزارشگیری خودرو ها",
    },
    {
        "path": "report/<int:pk>/",
        "view": views.report_detail,
        "name": "report_detail",
        "label": "پیمانکاران-جزئیات گزارش کارکرد خودرو",
    },
    {
        "path": "get_contractors_ajax/",
        "view": views.get_contractors_ajax,
        "name" : "get_contractors_ajax",
        "label": "پیمانکاران-دریافت پیمانکاران",
    },
    {
        "path": "get_contractor_employees_ajax/",
        "view": views.get_contractor_employees_ajax,
        "name": "get_contractor_employees_ajax",
        "label": "پیمانکاران-دریافت پیمانکاران",
    },
    {
        "path": "get-all-vehicles-ajax/",
        "view": views.get_all_vehicles_ajax,
        "name": "get_all_vehicles_ajax",
        "label": "پیمانکاران-دریافت خودروها",
    },
    {
        "path": "vehicle/<int:vehicle_id>/reports/",
        "view": views.vehicle_reports,
        "name": "vehicle_reports",
        "label": "پیمانکاران-گزارش‌های کارکرد خودرو",
    },
    {
        "path": "vehicle/<int:pk>/",
        "view": views.vehicle_detail,
        "name": "vehicle_detail",
        "label": "پیمانکاران-جزئیات خودرو",
    },
    {
        "path": "export-reports/",
        "view": views.export_reports_to_excel,
        "name": "export_reports",
        "label": "پیمانکاران-خروجی اکسل گزارش‌ها",
    },
    {
        "path": "export-vehicle-reports/<int:vehicle_id>/",
        "view": views.export_reports_to_excel,
        "name": "export_vehicle_reports",
        "label": "پیمانکاران-خروجی اکسل گزارش‌های خودرو",
    },
]


urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
]

