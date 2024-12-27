from django.urls import path
from . import views

app_name = 'contractor_management'
urlpatterns = [
    path('create-report/', views.create_report, name='create_report'),
]