from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """Hide disabled applications from Django admin's app/model lists."""
        from django.contrib import admin
        from .module_registry import get_module_states

        if getattr(admin.site, "_module_filter_installed", False):
            return

        original_get_app_list = admin.site.get_app_list

        def get_app_list(request, app_label=None):
            app_list = original_get_app_list(request, app_label)
            states = get_module_states()
            return [app for app in app_list if states.get(app["app_label"], True)]

        admin.site.get_app_list = get_app_list
        admin.site._module_filter_installed = True
