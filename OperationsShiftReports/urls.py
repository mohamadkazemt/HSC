from django.urls import path
from . import views

app_name = 'operations'
urlpatterns = [
    # مسیر ایجاد گزارش شیفت
    path('create-shift-report/', views.create_shift_report, name='create_shift_report'),
    path('loading-operations/', views.loading_operations_list, name='loading_operations_list'),
    path('operation/<int:pk>/', views.operation_detail, name='operation_detail'),
    #path('shift-report-success/', views.shift_report_success, name='shift_report_success'),
]

