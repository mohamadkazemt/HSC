from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/', views.notification_detail, name='notification_detail'),
    path('notification/<int:notification_id>/mark-read/', views.mark_notification_and_redirect, name='mark_notification_and_redirect'),
    path('notifications/mark-all-read/', views.mark_all_notifications_as_read, name='mark_all_notifications_read'),
    path('activities/', views.activity_list, name='activity_list'),  # اضافه کردن URL جدید
]