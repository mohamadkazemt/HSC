from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('settings/', views.site_settings_view, name='site_settings'),
]
