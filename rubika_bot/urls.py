from django.urls import path
from . import views

app_name = 'rubika_bot'

urlpatterns = [
    path('settings/', views.settings_view, name='settings'),
    path('settings/register-webhook/', views.action_register_webhook, name='register_webhook'),
    path('settings/webhook-info/', views.action_get_webhook_info, name='webhook_info'),
    path('settings/broadcast/', views.action_broadcast, name='broadcast'),
    path('quick-connect/', views.quick_connect, name='quick_connect'),
    path('generate-code/', views.generate_connection_code, name='generate_code'),
    path('webhook/', views.webhook_receiver, name='webhook'),
]