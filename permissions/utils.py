from django.urls import get_resolver
from django.apps import apps
from .models import UnitPermission, DepartmentPermission, PositionPermission


def get_all_views():
    """
    استخراج تمام ویوهای تعریف‌شده در پروژه، شامل الگوهای تو در تو.
    فقط ویوهایی که دارای نام هستند، بازگردانده می‌شوند.
    """
    views = []

    def extract_patterns(urlpatterns):
        for pattern in urlpatterns:
            if hasattr(pattern, "url_patterns"):  # بررسی وجود include
                extract_patterns(pattern.url_patterns)  # باز کردن الگوهای تو در تو
            elif hasattr(pattern, "name") and pattern.name:  # بررسی نام
                views.append(pattern.name)

    resolver = get_resolver()
    extract_patterns(resolver.url_patterns)

    return views


def get_all_models():
    """
    استخراج تمام مدل‌های تعریف‌شده در پروژه.
    نام مدل‌ها به صورت لیستی برگردانده می‌شود.
    """
    models = apps.get_models()
    return [model._meta.object_name for model in models]


def check_permission(user, view_name, permission_type="can_view"):
    """
    بررسی دسترسی کاربر به ویوی مشخص.
    دسترسی به صورت سلسله‌مراتبی بررسی می‌شود (واحد، بخش، سمت).

    Args:
        user: کاربر فعلی
        view_name: نام ویو
        permission_type: نوع دسترسی (can_view, can_add, can_edit, can_delete)

    Returns:
        True اگر دسترسی وجود داشته باشد، در غیر این صورت False.
    """
    user_profile = getattr(user, 'userprofile', None)
    if not user_profile:
        return False

    # بررسی دسترسی واحد
    if UnitPermission.objects.filter(
            unit=user_profile.unit,
            view_name=view_name,
            **{permission_type: True}
    ).exists():
        return True

    # بررسی دسترسی بخش
    if DepartmentPermission.objects.filter(
            department=user_profile.department,
            view_name=view_name,
            **{permission_type: True}
    ).exists():
        return True

    # بررسی دسترسی سمت
    if PositionPermission.objects.filter(
            position=user_profile.position,
            view_name=view_name,
            **{permission_type: True}
    ).exists():
        return True

    return False
