from django.urls import path
from . import views


app_name = 'accounts'
urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    #path('register/', views.register_view, name='register'),
    path('profile/', views.user_profile, name='profile'),
    path('settings/', views.edit_profile, name='settings'),
]