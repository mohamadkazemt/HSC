from django.urls import path
from . import views

app_name = 'hse_incidents'

urlpatterns = [
    path('incident_report/', views.report_incident, name='incident_report'),
    path('get_injury_types_ajax/', views.get_injury_types_ajax, name='get_injury_types_ajax'),
    path('list_reports/', views.list_reports, name='list_reports'),
    path('report_details/<int:report_id>/', views.report_details, name='report_details'),
    path('export_reports_excel/', views.export_reports_excel, name='export_reports_excel'),
    path('report_details_pdf/<int:report_id>/', views.report_details_pdf, name='report_details_pdf'),

]