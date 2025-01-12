from django.apps import AppConfig


class ContractorManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contractor_management'
    verbose_name = 'مدیریت پیمانکاران'


    def ready(self):
        import contractor_management.signals


