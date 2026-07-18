from django.http import Http404

from .module_registry import is_module_enabled, module_for_path


class ActiveModuleMiddleware:
    """Make a disabled module unreachable from public and admin URLs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        module_key = module_for_path(request.path_info)

        # Django admin model URLs always start with /admin/<app_label>/.
        if module_key is None and request.path_info.startswith("/admin/"):
            parts = request.path_info.strip("/").split("/")
            if len(parts) > 1:
                module_key = parts[1]

        if module_key and not is_module_enabled(module_key):
            raise Http404("این ماژول در حال حاضر غیرفعال است.")

        return self.get_response(request)
