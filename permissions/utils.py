from django.urls import get_resolver
from django.apps import apps
from .models import PartPermission, SectionPermission, PositionPermission, UnitGroupPermission, UserPermission
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
import logging
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


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


def get_all_views_with_labels():
    """
    استخراج تمام ویوهای تعریف‌شده در پروژه همراه با لیبل‌ها.
    """
    views_with_labels = []

    for app_name in apps.get_app_configs():
        try:
            module = __import__(f"{app_name.name}.urls", fromlist=["URLS_WITH_LABELS"])
            if hasattr(module, "URLS_WITH_LABELS"):
                views_with_labels.extend(module.URLS_WITH_LABELS)
        except ModuleNotFoundError:
            continue

    return views_with_labels


def get_all_models():
    """
    استخراج تمام مدل‌های تعریف‌شده در پروژه.
    نام مدل‌ها به صورت لیستی برگردانده می‌شود.
    """
    models = apps.get_models()
    return [model._meta.object_name for model in models]


def check_permission(user, view_name):
    """
    بررسی تمام انواع دسترسی کاربر به ویوی مشخص به صورت پویا.

    Args:
        user: کاربر فعلی
        view_name: نام ویو

    Returns:
        dict: شامل تمام انواع دسترسی موجود در دیتابیس برای این کاربر و ویو.
    """
    if user is None or isinstance(user, AnonymousUser):
        user_permissions = UserPermission.objects.none()  # Return an empty queryset
    else:
        user_permissions = UserPermission.objects.filter(
            group__in=user.groups.all(),
            permission__codename=view_name,
        )
    return user_permissions.exists()


def permission_required(view_name):
    """
    دکوریتور برای بررسی دسترسی کاربر به ویوها به صورت پویا.

    Args:
        view_name (str): نام ویو که دسترسی آن بررسی می‌شود.

    Returns:
        function: ویوی اصلی در صورت دسترسی.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            permissions = check_permission(request.user, view_name)
            if not any(permissions.values()):  # اگر هیچ دسترسی وجود نداشت
                raise PermissionDenied("شما اجازه دسترسی به این بخش را ندارید.")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def class_permission_required(view_name):
    def decorator(cls):
        original_dispatch = cls.dispatch

        @method_decorator(wraps(original_dispatch), name='dispatch')
        def new_dispatch(self, *args, **kwargs):
            # بررسی دسترسی‌ها
            permissions = check_permission(self.request.user, view_name)
            if not permissions:  # اگر دسترسی وجود نداشت
                raise PermissionDenied("شما اجازه دسترسی به این بخش را ندارید.")
            return original_dispatch(self, *args, **kwargs)

        cls.dispatch = new_dispatch
        return cls

    return decorator