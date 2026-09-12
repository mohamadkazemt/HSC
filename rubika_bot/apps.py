# rubika_bot/apps.py

from django.apps import AppConfig


class RubikaBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rubika_bot'

    def ready(self):
        from . import signals  # noqa: F401
