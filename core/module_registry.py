"""Registry and helpers for globally switchable business modules."""

from django.db.utils import OperationalError, ProgrammingError


# key: (Persian title, public URL prefixes). Keep infrastructure apps out of
# this list so an administrator can never lock themselves out of the site.
MODULES = {
    "anomalis": ("مدیریت آنومالی", ("/anomalis/",)),
    "meetings": ("مدیریت جلسات", ("/meetings/",)),
    "analytics": ("تحلیل و آمار", ()),
    "shift_manager": ("مدیریت شیفت", ("/shift-manager/",)),
    "BaseInfo": ("اطلاعات پایه", ("/baseinfo/",)),
    "OperationsShiftReports": ("گزارش شیفت عملیات", ("/OperationsShiftReports/",)),
    "dailyreport_hse": ("گزارش روزانه HSE", ("/dailyreport_hse/",)),
    "leave_reports": ("مرخصی و ترک کار", ("/leave_reports/",)),
    "contractor_management": ("مدیریت پیمانکاران", ("/contractor/",)),
    "hse_incidents": ("حوادث HSE", ("/hse_incidents/",)),
    "machine_checklist": ("چک‌لیست ماشین‌آلات", ("/machine-checklist/",)),
    "fire_reports": ("گزارش‌های آتش", ("/fire-reports/",)),
    "checklist_app": ("مدیریت چک‌لیست", ("/checklist_app/",)),
    "emergency_services": ("خدمات اورژانس", ("/emergency/",)),
    "fire_extinguisher_management": ("مدیریت کپسول آتش‌نشانی", ("/fire_extinguisher_management/",)),
    "rubika_bot": ("ربات روبیکا", ("/rubika-bot/", "/rubika_bot/")),
    "risk_assessment": ("ارزیابی ریسک", ("/risk/",)),
    "hse_docs": ("مستندات HSE", ("/hse-docs/",)),
    "corrective_actions": ("اقدامات اصلاحی", ("/corrective-actions/",)),
    "mining_operations": ("عملیات معدن", ("/mining-operations/",)),
    "gym_referrals": ("معرفی‌نامه باشگاه", ("/gym-referrals/",)),
    "message_center": ("مرکز پیام", ("/message-center/",)),
}


def get_module_title(module_key):
    return MODULES.get(module_key, (module_key, ()))[0]


def get_module_states():
    """Return all switches, defaulting safely to enabled before migration."""
    states = {key: True for key in MODULES}
    try:
        from .models import ModuleSetting

        states.update(dict(ModuleSetting.objects.values_list("module_key", "is_active")))
    except (OperationalError, ProgrammingError):
        pass
    return states


def is_module_enabled(module_key):
    if module_key not in MODULES:
        return True
    return get_module_states().get(module_key, True)


def module_for_path(path):
    for module_key, (_, prefixes) in MODULES.items():
        if any(path.startswith(prefix) for prefix in prefixes):
            return module_key
    return None
