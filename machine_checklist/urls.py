from django.urls import path
from . import views

app_name = 'machine_checklist'

URLS_WITH_LABELS = [
    {
        "path": "checklist_form/",
        "view": views.checklist_form_view,
        "name": "checklist_form",
        "label": "چک لیست ماشین_فرم چک لیست",
    },
    {
        "path": "get_questions/<int:machine_id>/",
        "view": views.get_questions,
        "name": "get_questions",
        "label": "چک لیست ماشین_دریافت سوالات",
    },
     {
        "path": "submit_checklist/",
        "view": views.submit_checklist,
        "name": "submit_checklist",
        "label": "چک لیست ماشین_ثبت چک لیست",
    },
    {
        "path": "checklist_list/",
        "view": views.checklist_list_view,
        "name": "checklist_list",
        "label": "چک لیست ماشین_لیست چک لیست‌ها",
    },
    {
        "path": "checklist_detail/<int:checklist_id>/",
        "view": views.checklist_detail_view,
        "name": "checklist_detail",
        "label": "چک لیست ماشین_جزئیات چک لیست",
    },
    {
        "path": "checklist/export/excel/",
        "view": views.export_checklists_excel,
        "name": "export_checklists_excel",
         "label": "چک لیست ماشین_خروجی اکسل چک لیست‌ها",
    },
]


urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
]