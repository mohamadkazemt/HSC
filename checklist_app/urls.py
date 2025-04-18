from django.urls import path
from . import views

app_name = 'checklist_app'

URLS_WITH_LABELS = [
    {
        "path": "",
        "view": views.general_checklist_list_view,
        "name": "general_checklist_list",
        "label": "چک لیست_صفحه اصلی چک لیست‌ها"
    },
    {
        "path": "new/",
        "view": views.general_checklist_form_view,
        "name": "general_checklist_form",
        "label": "چک لیست_فرم چک لیست جدید"
    },
    {
        "path": "<int:pk>/",
        "view": views.general_checklist_detail_view,
        "name": "general_checklist_detail",
        "label": "چک لیست_جزئیات چک لیست"
    },
    {
        "path": "get-questions/",
        "view": views.get_general_questions,
        "name": "get_general_questions",
        "label": "چک لیست_دریافت سوالات"
    },
    {
        "path": "submit-checklist/",
        "view": views.submit_general_checklist,
        "name": "submit_general_checklist",
        "label": "چک لیست_ثبت چک لیست"
    },
    {
        "path": "create-anomaly-from-failure/",
        "view": views.create_anomaly_from_failure_view,
        "name": "create_anomaly_from_failure",
        "label": "چک لیست_ایجاد ناهنجاری از خرابی"
    },
    {
        "path": "get-followup-users/",
        "view": views.get_followup_users,
        "name": "get_followup_users",
        "label": "چک لیست_دریافت کاربران پیگیری"
    },
    {
        "path": "export-excel/",
        "view": views.export_general_checklists_excel,
        "name": "export_general_checklists_excel",
        "label": "چک لیست_خروجی اکسل"
    },
    {
        "path": "questions/",
        "view": views.general_question_list_view,
        "name": "general_question_list",
        "label": "چک لیست_لیست سوالات"
    },
    {
        "path": "questions/add/",
        "view": views.general_question_form_view,
        "name": "general_question_form",
        "label": "چک لیست_افزودن سوال"
    },
    {
        "path": "questions/edit/<int:pk>/",
        "view": views.general_question_edit_view,
        "name": "general_question_edit",
        "label": "چک لیست_ویرایش سوال"
    },
    {
        "path": "questions/delete/",
        "view": views.general_question_delete_view,
        "name": "general_question_delete",
        "label": "چک لیست_حذف سوال"
    },
    {
        "path": "questions/import/",
        "view": views.import_questions_view,
        "name": "import_questions",
        "label": "چک لیست_ایمپورت سوالات"
    }
]

urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
] 