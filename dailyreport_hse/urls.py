from django.urls import path
from . import views


app_name = "hsec"
urlpatterns = [
    path('create/', views.create_daily_report, name='create_daily_report'),
    path('list/', views.report_list, name='report_list'),
    path('detail/<int:pk>/', views.report_detail, name='report_detail'),
]
