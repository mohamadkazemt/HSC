from django.urls import path
from . import views


app_name = "hsec"
urlpatterns = [
    path('create/', views.create_daily_report, name='create_daily_report'),

]
