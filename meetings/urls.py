from django.urls import path
from . import views

app_name = 'meetings'

urlpatterns = [
    path('', views.MeetingListView.as_view(), name='meeting_list'),
    path('create/', views.MeetingCreateView.as_view(), name='meeting_create'),
    path('<int:pk>/', views.MeetingDetailView.as_view(), name='meeting_detail'),
    path('<int:pk>/edit/', views.MeetingUpdateView.as_view(), name='meeting_edit'),
    path('<int:pk>/delete/', views.MeetingDeleteView.as_view(), name='meeting_delete'),
    path('<int:pk>/cancel/', views.cancel_meeting, name='meeting_cancel'),
    path('report/', views.meeting_report, name='meeting_report'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('export/', views.meeting_export, name='meeting_export'),
    path('calendar/', views.meeting_calendar, name='meeting_calendar'),
] 