from typing import Optional
from .models import SiteSettings
import jdatetime


def site_settings(request):
    """Inject the singleton SiteSettings into all templates as `site_settings`."""
    try:
        settings_obj: Optional[SiteSettings] = SiteSettings.objects.first()
    except Exception:
        # In case migrations aren't applied yet
        settings_obj = None
    return {"site_settings": settings_obj}


def today_jalali(request):
    """Inject today's Jalali date into all templates for date picker maxDate restriction."""
    try:
        today = jdatetime.date.today()
        return {"today_jalali": today.strftime('%Y/%m/%d')}
    except Exception:
        return {"today_jalali": None}
