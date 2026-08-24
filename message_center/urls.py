from django.urls import path

from . import views

app_name = "message_center"

# ``name`` is the grantable permission string managed by the central
# permissions app and must match the value passed to @permission_required
# in the view; ``url_name`` keeps the URL name stable for reverse().
URLS_WITH_LABELS = [
    {
        "path": "leave-reminders/",
        "view": views.leave_reminders,
        "url_name": "leave_reminders",
        "name": "send_leave_reminders",
        "label": "پیام_یادآوری تأیید مرخصی",
    },
]

urlpatterns = [
    path(item["path"], item["view"], name=item.get("url_name", item["name"]))
    for item in URLS_WITH_LABELS
]
