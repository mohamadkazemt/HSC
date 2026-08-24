from django.urls import path

from . import views

app_name = "message_center"

URLS_WITH_LABELS = [
    {
        "path": "leave-reminders/",
        "view": views.leave_reminders,
        "name": "leave_reminders",
        "label": "پیام_یادآوری تأیید مرخصی",
    },
]

urlpatterns = [path(item["path"], item["view"], name=item["name"]) for item in URLS_WITH_LABELS]
