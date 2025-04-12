from django.urls import path
from . import views

app_name = 'checklist_app'

urlpatterns = [
    path('', views.checklist_list_view, name='checklist_list'),
    path('new/', views.checklist_form_view, name='checklist_form'),
    path('<int:pk>/', views.checklist_detail_view, name='checklist_detail'),
    path('get-questions/', views.get_questions, name='get_questions'),
    path('submit-checklist/', views.submit_checklist, name='submit_checklist'),
    path('create-anomaly-from-failure/', views.create_anomaly_from_failure_view, name='create_anomaly_from_failure'),
    path('get-followup-users/', views.get_followup_users, name='get_followup_users'),
    path('export-excel/', views.export_checklists_excel, name='export_checklists_excel'),
    path('questions/', views.question_list_view, name='question_list'),
    path('questions/add/', views.question_form_view, name='question_form'),
    path('questions/edit/<int:pk>/', views.question_edit_view, name='question_edit'),
    path('questions/delete/', views.question_delete_view, name='question_delete'),
] 