"""Short public URLs for the dependent-information portal (used in SMS/Rubika links)."""

from django.urls import path

from . import dependent_views as views

app_name = 'dependents'

urlpatterns = [
    path('', views.dependent_portal, name='home'),
    path('send-code/', views.dependent_portal_send_otp, name='send_code'),
    path('verify-code/', views.dependent_portal_verify_otp, name='verify_code'),
    path('logout/', views.dependent_portal_logout, name='logout'),
    path('info/', views.dependent_portal_home, name='info'),
    path('info/add/', views.dependent_portal_add, name='add'),
    path('info/<int:pk>/edit/', views.dependent_portal_edit, name='edit'),
    path('info/<int:pk>/delete/', views.dependent_portal_delete, name='delete'),
]
