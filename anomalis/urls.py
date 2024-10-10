from tkinter.font import names
from django.urls import path, include
from . import views
from .views import get_anomalydescription, get_hse_type, get_corrective_action

app_name = 'anomalis'
urlpatterns = [
    path('', views.anomalis, name='anomalis'),
    path('listanomalies', views.anomaly_list, name='list'),
    path('toggle-status/<int:pk>/', views.toggle_status, name='toggle_status'),
    path('edit_anomaly/<int:pk>/', views.edit_anomaly, name='edit'),
    path('delete_anomaly/<int:pk>/', views.delete_anomaly, name='delete'),
    path('get-anomalydescription/', get_anomalydescription, name='get_anomalydescription'),
    path('get-hse-type/<int:description_id>/', get_hse_type, name='get_hse_type'),
    path('get-corrective-action/<int:description_id>/', get_corrective_action, name='get_corrective_action'),

]
