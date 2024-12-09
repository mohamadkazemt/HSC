from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_shift_report, name='create_shift_report'),
]
