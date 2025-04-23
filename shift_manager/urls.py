from django.urls import path
from .views import shift_calendar_view


app_name = 'shift_manager'

urlpatterns = [
    path('calendar/', shift_calendar_view, name='shift_calendar'),
]