from django.urls import path
from .views import shift_calendar_view, initial_shift_setup_ajax, export_shift_calendar_excel


app_name = 'shift_manager'

urlpatterns = [
    path('calendar/', shift_calendar_view, name='shift_calendar'),
    path('api/initial-setup/', initial_shift_setup_ajax, name='initial_shift_setup_ajax'),
    path('export-excel/', export_shift_calendar_excel, name='export_shift_calendar_excel'),
]