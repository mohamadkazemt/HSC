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
]

urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
]