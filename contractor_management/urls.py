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
        "path": "get_contractors_ajax/",
        "view": views.get_contractors_ajax,
        "name" : "get_contractors_ajax",


    },

]


urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS

]