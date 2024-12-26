from django.urls import path
from . import views

app_name = "permissions"

urlpatterns = [
    path("manage/", views.manage_access, name="manage_access"),
    path('list/', views.list_permissions, name='list_permissions'),
    path('edit/<int:permission_id>/', views.edit_permission, name='edit_permission'),
    path('delete/<int:permission_id>/', views.delete_permission, name='delete_permission'),
]
