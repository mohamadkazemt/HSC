from django.urls import path
from . import views

urlpatterns = [
    path("manage/", views.manage_access, name="manage_access"),
]
