# rubika_bot/apps.py

from django.apps import AppConfig
import nest_asyncio

class RubikaBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rubika_bot'

    def ready(self):
        # این خط مشکل RuntimeError: Timeout context manager را حل می‌کند
        nest_asyncio.apply()

        # Import signal handlers
        from . import signals  # noqa: F401