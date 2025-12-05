from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('settings/', views.site_settings_view, name='site_settings'),
    path('ai-settings/', views.ai_settings_view, name='ai_settings'),
    path('ai-settings/test-connection/', views.ai_test_connection, name='ai_test_connection'),
]
