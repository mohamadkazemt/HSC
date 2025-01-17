from django.urls import path
from .views import (
    CreateDailyReportView,
    DailyReportFormView,
    DailyReportListView,
    DailyReportDetailView,
    daily_report_pdf_view,
)

app_name = "dailyreport_hse"

URLS_WITH_LABELS = [
    {
        "path": "API/",
        "view": CreateDailyReportView.as_view(),
        "name": "create_daily_report",
        "label": "گزارش روزانه HSE_ایجاد گزارش روزانه",
    },
    {
        "path": "create/",
        "view": DailyReportFormView.as_view(),
        "name": "daily_report_form",
        "label": "گزارش روزانه HSE_فرم گزارش روزانه",
    },
    {
        "path": "list/",
        "view": DailyReportListView.as_view(),
        "name": "daily_report_list",
        "label": "گزارش روزانه HSE_لیست گزارش‌ها",
    },
    {
        "path": "detail/<int:pk>/",
        "view": DailyReportDetailView.as_view(),
        "name": "daily_report_detail",
        "label": "گزارش روزانه HSE_جزئیات گزارش",
    },
    {
        "path": "detail/<int:pk>/pdf/",
        "view": daily_report_pdf_view,
        "name": "daily_report_pdf",
        "label": "گزارش روزانه HSE_دریافت PDF گزارش",
    },
]

# تبدیل URLS_WITH_LABELS به urlpatterns
urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
]
