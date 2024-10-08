from tkinter.font import names
from django.urls import path, include
from . import views

app_name = 'anomalis'
urlpatterns = [
    path('', views.anomalis, name='anomalis'),
    path('listanomalies', views.anomaly_list, name='list'),
    path('toggle-status/<int:pk>/', views.toggle_status, name='toggle_status'),
    path('edit_anomaly/<int:pk>/', views.edit_anomaly, name='edit'),
    path('delete_anomaly/<int:pk>/', views.delete_anomaly, name='delete'),

]