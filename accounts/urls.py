from django.urls import path
from . import views


app_name = 'accounts'

urlpatterns = [
    path('', views.user_login, name='login'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    #path('register/', views.register_view, name='register'),
    path('profile/', views.user_profile, name='profile'),
    path('settings/', views.edit_profile, name='settings'),
    path('reset-password/sms/', views.send_reset_code, name='send_reset_code'),
    path('reset-password/confirm/', views.confirm_reset_code, name='reset_password_confirm'),
    path('get_users_ajax/', views.get_users_ajax, name='get_users_ajax'),
    path('driver-license/', views.driver_license, name='driver_license'),
    # Personnel management
    path('personnel/', views.personnel_list, name='personnel_list'),
    path('personnel/<int:user_id>/edit/', views.personnel_edit, name='personnel_edit'),
    path('personnel/import/', views.personnel_import, name='personnel_import'),
    path('personnel/export/', views.personnel_export, name='personnel_export'),
    # Personnel cascading filter APIs
    path('personnel/api/parts/', views.api_parts_by_section, name='personnel_api_parts'),
    path('personnel/api/unit-groups/', views.api_unit_groups_by_part, name='personnel_api_unit_groups'),
    path('personnel/api/positions/', views.api_positions_by_unit_group, name='personnel_api_positions'),
]
