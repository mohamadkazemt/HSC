from django.urls import path
from . import views

app_name = 'fire_reports'

urlpatterns = [
    path('', views.fire_report_list, name='report_list'),
    path('create/', views.fire_report_create, name='report_create'),
    path('<int:pk>/', views.fire_report_detail, name='report_detail'),
    path('<int:pk>/edit/', views.fire_report_edit, name='report_edit'),
    path('<int:pk>/delete/', views.fire_report_delete, name='report_delete'),
    path('<int:pk>/approve/', views.fire_report_approve, name='report_approve'),
] 