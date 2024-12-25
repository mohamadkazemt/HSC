from django.urls import path, include
from . import views
from .views import get_anomalydescription, get_hse_type, get_corrective_action
from . import views

app_name = 'anomalis'

URLS_WITH_LABELS = [
    {"path": "", "view": views.anomalis, "name": "anomalis", "label": "صفحه اصلی ناهنجاری‌ها"},
    {"path": "listanomalies", "view": views.anomaly_list, "name": "list", "label": "لیست ناهنجاری‌ها"},
    {"path": "get-anomalydescription/", "view": get_anomalydescription, "name": "get_anomalydescription", "label": "دریافت توضیحات ناهنجاری"},
    {"path": "get-hse-type/<int:description_id>/", "view": get_hse_type, "name": "get_hse_type", "label": "دریافت نوع HSE"},
    {"path": "get-corrective-action/<int:description_id>/", "view": get_corrective_action, "name": "get_corrective_action", "label": "دریافت اقدامات اصلاحی"},
    {"path": "anomaly/<int:pk>/", "view": views.anomaly_detail_view, "name": "anomaly_detail", "label": "جزئیات ناهنجاری"},
    {"path": "anomaly/<int:pk>/request-safe/", "view": views.request_safe, "name": "request_safe", "label": "درخواست ایمنی برای ناهنجاری"},
    {"path": "anomaly/<int:pk>/approve/", "view": views.approve_safe, "name": "approve_safe", "label": "تأیید ایمنی ناهنجاری"},
    {"path": "anomaly/<int:pk>/reject/", "view": views.reject_safe, "name": "reject_safe", "label": "رد ایمنی ناهنجاری"},
    {"path": "export-anomalies/", "view": views.export_anomalies_to_excel, "name": "export_anomalies_to_excel", "label": "صادرات ناهنجاری‌ها به اکسل"},
    {"path": "get-sections/", "view": views.get_sections, "name": "get_sections", "label": "دریافت بخش‌ها"},
    {"path": "anomaly/<int:pk>/pdf/", "view": views.anomaly_pdf_view, "name": "anomaly_pdf", "label": "دانلود PDF ناهنجاری"},
]

urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
]
