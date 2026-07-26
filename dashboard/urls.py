from django.urls import path
from . import views

app_name = 'dashboard'

URLS_WITH_LABELS = [
    {
        'name': 'dashboard_personnel_statistics',
        'label': 'داشبورد_آمار مدیریتی پرسنل',
    },
    {
        'name': 'dashboard_dependent_statistics',
        'label': 'داشبورد_آمار مدیریتی افراد تحت تکفل',
    },
]

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('admin-overview/', views.admin_overview, name='admin_overview'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/', views.notification_detail, name='notification_detail'),
    path('notification/<int:notification_id>/mark-read/', views.mark_notification_and_redirect, name='mark_notification_and_redirect'),
    path('notifications/mark-all-read/', views.mark_all_notifications_as_read, name='mark_all_notifications_read'),
    path('activities/', views.activity_list, name='activity_list'),  # اضافه کردن URL جدید
]
