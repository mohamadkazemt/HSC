from django.urls import path
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
    }
]

urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
]
