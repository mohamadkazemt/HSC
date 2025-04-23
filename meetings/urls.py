from django.urls import path
from . import views

app_name = 'meetings'

URLS_WITH_LABELS = [
    {
        "path": "",
        "view": views.MeetingListView.as_view(),
        "name": "meeting_list",
        "label": "جلسات_لیست جلسات"
    },
    {
        "path": "create/",
        "view": views.MeetingCreateView.as_view(),
        "name": "meeting_create",
        "label": "جلسات_ایجاد جلسه جدید"
    },
    {
        "path": "<int:pk>/",
        "view": views.MeetingDetailView.as_view(),
        "name": "meeting_detail",
        "label": "جلسات_جزئیات جلسه"
    },
    {
        "path": "<int:pk>/edit/",
        "view": views.MeetingUpdateView.as_view(),
        "name": "meeting_edit",
        "label": "جلسات_ویرایش جلسه"
    },
    {
        "path": "<int:pk>/delete/",
        "view": views.MeetingDeleteView.as_view(),
        "name": "meeting_delete",
        "label": "جلسات_حذف جلسه"
    },
    {
        "path": "<int:pk>/cancel/",
        "view": views.cancel_meeting,
        "name": "meeting_cancel",
        "label": "جلسات_لغو جلسه"
    },
    {
        "path": "report/",
        "view": views.meeting_report,
        "name": "meeting_report",
        "label": "جلسات_گزارش جلسه"
    },
    {
        "path": "notification/<int:notification_id>/read/",
        "view": views.mark_notification_read,
        "name": "mark_notification_read",
        "label": "جلسات_خواندن اعلان"
    },
    {
        "path": "export/",
        "view": views.meeting_export,
        "name": "meeting_export",
        "label": "جلسات_صادرات جلسات"
    },
    {
        "path": "calendar/",
        "view": views.meeting_calendar,
        "name": "meeting_calendar",
        "label": "جلسات_تقویم جلسات"
    },


]

urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
]