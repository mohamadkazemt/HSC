from django.urls import path
from . import views

urlpatterns = [
    # مسیر ایجاد گزارش شیفت
    path('create-shift-report/', views.create_shift_report, name='create_shift_report'),

    # مسیر نمایش موفقیت آمیز بودن ثبت گزارش شیفت
    #path('shift-report-success/', views.shift_report_success, name='shift_report_success'),
]
