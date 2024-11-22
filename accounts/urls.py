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
]