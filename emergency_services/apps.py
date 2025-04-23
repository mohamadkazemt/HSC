from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EmergencyServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'emergency_services'
    verbose_name = _('اورژانس معدن')
    
    def ready(self):
        import emergency_services.signals 