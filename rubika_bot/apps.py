# rubika_bot/apps.py

from django.apps import AppConfig
import nest_asyncio


class RubikaBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rubika_bot'

    def ready(self):
        nest_asyncio.apply()
        from . import signals  # noqa: F401