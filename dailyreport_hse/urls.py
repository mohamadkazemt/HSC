from django.urls import path
from . import views

app_name = "dailyreport_hse"

urlpatterns = [
    path('create/', views.create_daily_report, name="create_daily_report"),
]
