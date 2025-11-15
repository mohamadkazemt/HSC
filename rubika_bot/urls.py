from django.urls import path
from . import views

app_name = 'rubika_bot'

urlpatterns = [
    path('settings/', views.settings_view, name='settings'),
    path('settings/register-webhook/', views.action_register_webhook, name='register_webhook'),
    path('settings/webhook-info/', views.action_get_webhook_info, name='webhook_info'),
    path('settings/test-proxy/', views.action_test_proxy, name='test_proxy'),
    path('settings/broadcast/', views.action_broadcast, name='broadcast'),
    path('settings/disconnect/<str:chat_id>/', views.action_disconnect_user, name='disconnect_user'),
    path('settings/logs/', views.get_webhook_logs, name='get_logs'),
    path('settings/logs/clear/', views.clear_webhook_logs, name='clear_logs'),
    path('settings/logs/export/', views.export_webhook_logs, name='export_logs'),
    path('connect/', views.connect_page, name='connect_page'),
    path('quick-connect/', views.quick_connect, name='quick_connect'),
    path('generate-code/', views.generate_connection_code, name='generate_code'),
    path('get-connection-link/', views.get_connection_link, name='get_connection_link'),
    path('webhook/', views.webhook_receiver, name='webhook'),
    path('health/', views.health_check, name='health_check'),
    path('c/<str:short_code>/', views.short_link_redirect, name='short_link'),
]