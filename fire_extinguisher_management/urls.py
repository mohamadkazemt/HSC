from django.urls import path
from . import views

app_name = 'fire_extinguisher_management'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Fire Extinguisher Management
    path('extinguishers/', views.extinguisher_list, name='extinguisher_list'),
    path('extinguishers/create/', views.extinguisher_create, name='extinguisher_create'),
    path('extinguishers/<int:pk>/', views.extinguisher_detail, name='extinguisher_detail'),
    path('extinguishers/<int:pk>/edit/', views.extinguisher_edit, name='extinguisher_edit'),
    path('extinguishers/<int:pk>/replace/', views.extinguisher_replace, name='extinguisher_replace'),
    path('extinguishers/<int:pk>/change-location/', views.extinguisher_change_location, name='extinguisher_change_location'),

    # Service Records
    path('extinguishers/<int:extinguisher_pk>/service-records/create/', views.service_record_create, name='service_record_create'),

    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/mark-read/', views.mark_notification_read, name='mark_notification_read'),

    # Extinguisher Details API
    path('extinguishers/<int:pk>/details/', views.extinguisher_details_api, name='extinguisher_details_api'),
] 