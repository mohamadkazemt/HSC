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
    {
        "path": "get_personnels/",
        "view": views.get_personnels,
        "name": "get_personnels",
        "label": "مرخصی_دریافت لیست پرسنل",
    },
    {
        "path": "delete_leave/<int:leave_id>/",
        "view": views.delete_leave,
        "name": "delete_leave",
        "label": "مرخصی_حذف مرخصی",
    },
    {
        "path": "add_leave/",
        "view": views.add_leave,
        "name": "add_leave",
        "label": "مرخصی_افزودن مرخصی",
    },
    {
        "path": "export-excel/",
        "view": views.export_shift_reports_excel,
        "name": "export_shift_reports_excel",
        "label": "مرخصی_خروجی اکسل گزارش‌های شیفت",
    },
    {
        "path": "toggle-status/<int:report_id>/",
        "view": views.toggle_status,
        "name": "toggle_status",
        "label": "مرخصی_تغییر وضعیت مرخصی",
    },
    {
        "path": "toggle-registration/<int:report_id>/",
        "view": views.toggle_registration,
        "name": "toggle_registration",
        "label": "مرخصی_تغییر وضعیت ثبت مرخصی",
    },
]

urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
]
