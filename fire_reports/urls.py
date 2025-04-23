from django.urls import path
from . import views

app_name = 'fire_reports'

URLS_WITH_LABELS = [
    {
        "path": "list/",
        "view": views.fire_report_list,
        "name": "report_list",
        "label": "آتش‌نشانی_لیست گزارشات"
    },
    {
        "path": "create/",
        "view": views.fire_report_create,
        "name": "report_create",
        "label": "آتش‌نشانی_ایجاد گزارش جدید"
    },
    {
        "path": "detail/<int:pk>/",
        "view": views.fire_report_detail,
        "name": "report_detail",
        "label": "آتش‌نشانی_جزئیات گزارش"
    },
    {
        "path": "edit/<int:pk>/",
        "view": views.fire_report_edit,
        "name": "report_edit",
        "label": "آتش‌نشانی_ویرایش گزارش"
    },
    {
        "path": "delete/<int:pk>/",
        "view": views.fire_report_delete,
        "name": "report_delete",
        "label": "آتش‌نشانی_حذف گزارش"
    },
    {
        "path": "approve/<int:pk>/",
        "view": views.fire_report_approve,
        "name": "report_approve",
        "label": "آتش‌نشانی_تأیید گزارش"
    },
    {
        "path": "pdf/<int:pk>/",
        "view": views.fire_report_pdf,
        "name": "report_pdf",
        "label": "آتش‌نشانی_دانلود PDF گزارش"
    },
]

# تبدیل URLS_WITH_LABELS به urlpatterns
urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
]

# اضافه کردن URL های API
urlpatterns.append(
    path('api/emergency-vehicle/<int:vehicle_id>/', views.get_vehicle_info, name='get_vehicle_info')
) 