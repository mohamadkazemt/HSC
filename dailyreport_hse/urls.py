from django.urls import path
from .views import CreateDailyReportView, DailyReportFormView, DailyReportListView, DailyReportDetailView

app_name = "dailyreport_hse"

urlpatterns = [
    path('API/', CreateDailyReportView.as_view(), name="create_daily_report"),
    path('create/', DailyReportFormView.as_view(), name="daily_report_form"),
    path('list/', DailyReportListView.as_view(), name="daily_report_list"),
    path('detail/<int:pk>/', DailyReportDetailView.as_view(), name="daily_report_detail"),
]
