from django.urls import path
from . import views


app_name = 'accounts'

urlpatterns = [
    path('', views.user_login, name='login'),
    path('login/', views.user_login, name='login'),
    path('login/otp/send/', views.send_login_otp, name='send_login_otp'),
    path('login/otp/verify/', views.verify_login_otp, name='verify_login_otp'),
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
    path('personnel/add/', views.personnel_add, name='personnel_add'),
    path('personnel/<int:user_id>/edit/', views.personnel_edit, name='personnel_edit'),
    path('personnel/import/', views.personnel_import, name='personnel_import'),
    path('personnel/export/', views.personnel_export, name='personnel_export'),
    # Personnel cascading filter APIs
    path('personnel/api/parts/', views.api_parts_by_section, name='personnel_api_parts'),
    path('personnel/api/unit-groups/', views.api_unit_groups_by_part, name='personnel_api_unit_groups'),
    path('personnel/api/positions/', views.api_positions_by_unit_group, name='personnel_api_positions'),
    # Organization management
    path('organization/', views.organization_manage, name='organization_manage'),
    path('organization/add/', views.organization_add, name='organization_add'),
    path('organization/<str:entity_type>/<int:entity_id>/edit/', views.organization_edit, name='organization_edit'),
    path('organization/<str:entity_type>/<int:entity_id>/delete/', views.organization_delete, name='organization_delete'),
    path('organization/<str:entity_type>/merge/', views.organization_merge, name='organization_merge'),
    # Organizational chart
    path('organization-chart/', views.organization_chart, name='organization_chart'),
    # Payslip management
    path('payslips/upload/', views.batch_payslip_upload, name='batch_payslip_upload'),
    path('payslips/archive/', views.payslip_archive, name='payslip_archive'),
    path('payslips/<int:payslip_id>/download/', views.payslip_download, name='payslip_download'),
]
