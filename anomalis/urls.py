from django.urls import path, include
from . import views
from .views import get_anomalydescription, get_hse_type, get_corrective_action
from . import views

app_name = 'anomalis'
urlpatterns = [
    path('', views.anomalis, name='anomalis'),
    path('listanomalies', views.anomaly_list, name='list'),
    path('get-anomalydescription/', get_anomalydescription, name='get_anomalydescription'),
    path('get-hse-type/<int:description_id>/', get_hse_type, name='get_hse_type'),
    path('get-corrective-action/<int:description_id>/', get_corrective_action, name='get_corrective_action'),
    path('anomaly/<int:pk>/', views.anomaly_detail_view, name='anomaly_detail'),
    path('anomaly/<int:pk>/request-safe/', views.request_safe, name='request_safe'),
    path('anomaly/<int:pk>/approve/', views.approve_safe, name='approve_safe'),
    path('anomaly/<int:pk>/reject/', views.reject_safe, name='reject_safe'),
    path('export-anomalies/', views.export_anomalies_to_excel, name='export_anomalies_to_excel'),

]
