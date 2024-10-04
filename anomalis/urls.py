from django.urls import path, include
from . import views

app_name = 'anomalis'
urlpatterns = [
    path('', views.anomalis, name='anomalis'),


]