from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/mark/<int:notification_id>/', views.mark_notification_and_redirect, name='mark_notification_and_redirect'),
]
