from django.urls import path
from . import views

app_name = 'leave_reports'

URLS_WITH_LABELS = [
    {
        "path": "shift_report/",
        "view": views.create_shift_report,
        "name": "shift_report",
        "label": "مرخصی_ایجاد گزارش شیفت",
    },
    {
        "path": "shift_report_list/",
        "view": views.shift_report_list,
        "name": "shift_report_list",
        "label": "مرخصی_لیست گزارش‌های شیفت",
    },
    {
        "path": "shift_report/<int:report_id>/",
        "view": views.shift_report_detail,
        "name": "shift_report_detail",
        "label": "مرخصی_جزئیات گزارش شیفت",
    },
    {
        "path": "shift_report/<int:pk>/pdf/",
        "view": views.shift_report_pdf_view,
        "name": "shift_report_pdf",
        "label": "مرخصی_دانلود PDF گزارش شیفت",
    },
]

urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
]
