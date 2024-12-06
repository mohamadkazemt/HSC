from django.urls import path
from . import views

app_name = 'leave_reports'
urlpatterns = [
    path('shift_report/', views.create_shift_report, name='shift_report'),
    path('shift_report_list/', views.shift_report_list, name='shift_report_list'),
    path('shift_report/<int:report_id>/', views.shift_report_detail, name='shift_report_detail'),
    path('shift_report/<int:pk>/pdf/', views.shift_report_pdf_view, name='shift_report_pdf'),

]
