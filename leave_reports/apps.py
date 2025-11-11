from django.apps import AppConfig


class LeaveReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'leave_reports'
    
    def ready(self):
        import leave_reports.signals  # noqa
