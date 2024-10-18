from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('mark-notifications-read/', views.mark_notifications_as_read, name='mark_notifications_as_read'),
]
