from django.apps import AppConfig


class FireExtinguisherManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fire_extinguisher_management'
    verbose_name = 'مدیریت کپسول‌های آتش‌نشانی'

    def ready(self):
        try:
            import fire_extinguisher_management.signals  # noqa
        except ImportError:
            pass
