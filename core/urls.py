from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # داشبورد لاگ‌ها
    path('logs/', views.log_dashboard, name='log_dashboard'),
    
    # نمایش لاگ خاص
    path('logs/<str:log_name>/', views.view_log, name='view_log'),
    
    # دانلود لاگ
    path('logs/<str:log_name>/download/', views.download_log, name='download_log'),
    
    # پاک کردن لاگ
    path('logs/<str:log_name>/clear/', views.clear_log, name='clear_log'),
    
    # API آمار لاگ‌ها
    path('api/logs/stats/', views.log_stats_api, name='log_stats_api'),
]

# Handler برای خطا 403
handler403 = views.custom_403_handler
