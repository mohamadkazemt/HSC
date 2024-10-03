from django.urls import path
from . import views

app_name = 'anomalis'
urlpatterns = [
    path('', views.anomalis, name='anomalis'),
    path('location/', views.location, name='location'),
    path('anomalytype/', views.anomalytype, name='anomalytype'),
    path('location/delete/<int:pk>/', views.delete_location, name='delete_location'),
    #path('anomalytype/delete/<int:pk>/', views.delete_anomalytype, name='delete_anomalytype'),
    path('location/edit/<int:pk>/', views.location_edit, name='location_edit'),

]