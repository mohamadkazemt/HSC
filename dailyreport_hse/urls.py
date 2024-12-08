from django.urls import path
from .views import HSEWizard

app_name = 'hse'

urlpatterns = [
    path('new-report/', HSEWizard.as_view(), name='new_report'),
]
