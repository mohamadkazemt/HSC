from typing import Optional
from .models import SiteSettings


def site_settings(request):
    """Inject the singleton SiteSettings into all templates as `site_settings`."""
    try:
        settings_obj: Optional[SiteSettings] = SiteSettings.objects.first()
    except Exception:
        # In case migrations aren't applied yet
        settings_obj = None
    return {"site_settings": settings_obj}
