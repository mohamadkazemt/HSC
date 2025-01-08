from django.urls import path
from . import views

app_name = 'machine_checklist'

urlpatterns = [
    path('checklist_form/', views.checklist_form_view, name='checklist_form'),
    path('get_questions/<int:machine_id>/', views.get_questions, name='get_questions'),
    path('submit_checklist/', views.submit_checklist, name='submit_checklist'),
    path('checklist_list/', views.checklist_list_view, name='checklist_list'),
    path('checklist_detail/<int:checklist_id>/', views.checklist_detail_view, name='checklist_detail'),
    path('checklist/export/excel/', views.export_checklists_excel, name='export_checklists_excel'),  # Add this line
]