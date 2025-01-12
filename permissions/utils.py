from django.urls import get_resolver
from django.apps import apps
from .models import PartPermission, SectionPermission, PositionPermission, UnitGroupPermission, UserPermission
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
import logging
import logging

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
    user_profile = getattr(user, 'userprofile', None)

    logger.debug(f"Checking permissions for user: {user.username} (ID: {user.id}), view: {view_name}")

    if not user_profile:
        logger.debug(f"User {user.username} does not have a user profile.")

        user_permissions = UserPermission.objects.filter(
            user=user,
            view_name=view_name
        ).first()
        if user_permissions:
            user_permission_values = {
                field.name: getattr(user_permissions, field.name)
                for field in UserPermission._meta.fields
                if field.name.startswith("can_")
            }
            logger.debug(f"user permissions found: {user_permission_values}")
            return user_permission_values
        else:
            logger.debug(f"No user permissions found for user: {user} and view: {view_name}")
        return {}

    logger.debug(
        f"User profile found: Unit={user_profile.part}, Department={user_profile.section}, Position={user_profile.position},UnitGroup={user_profile.unit_group}")

    permissions = {}

    # بررسی دسترسی قسمت
    if user_profile.part:
        part_permissions = PartPermission.objects.filter(
            part=user_profile.part,
            view_name=view_name
        ).first()
        if part_permissions:
            part_permission_values = {
                field.name: getattr(part_permissions, field.name)
                for field in PartPermission._meta.fields
                if field.name.startswith("can_")
            }
            logger.debug(f"part permissions found: {part_permission_values}")
            permissions.update(part_permission_values)
        else:
            logger.debug(f"No part permissions found for part: {user_profile.part} and view: {view_name}")

    # بررسی دسترسی بخش
    if user_profile.section:
        section_permissions = SectionPermission.objects.filter(
            section=user_profile.section,
            view_name=view_name
        ).first()
        if section_permissions:
            section_permission_values = {
                field.name: getattr(section_permissions, field.name)
                for field in SectionPermission._meta.fields
                if field.name.startswith("can_")
            }
            logger.debug(f"section permissions found: {section_permission_values}")
            permissions.update(section_permission_values)
        else:
            logger.debug(f"No section permissions found for section: {user_profile.section} and view: {view_name}")

    # بررسی دسترسی گروه
    if user_profile.unit_group:
        unit_group_permissions = UnitGroupPermission.objects.filter(
            unit_group=user_profile.unit_group,
            view_name=view_name
        ).first()
        if unit_group_permissions:
            unit_group_permission_values = {
                field.name: getattr(unit_group_permissions, field.name)
                for field in UnitGroupPermission._meta.fields
                if field.name.startswith("can_")
            }
            logger.debug(f"unit_group permissions found: {unit_group_permission_values}")
            permissions.update(unit_group_permission_values)
        else:
            logger.debug(
                f"No unit_group permissions found for unit_group: {user_profile.unit_group} and view: {view_name}")

    # بررسی دسترسی سمت
    if user_profile.position:
        position_permissions = PositionPermission.objects.filter(
            position=user_profile.position,
            view_name=view_name
        ).first()
        if position_permissions:
            position_permission_values = {
                field.name: getattr(position_permissions, field.name)
                for field in PositionPermission._meta.fields
                if field.name.startswith("can_")
            }
            logger.debug(f"Position permissions found: {position_permission_values}")
            permissions.update(position_permission_values)
        else:
            logger.debug(f"No position permissions found for position: {user_profile.position} and view: {view_name}")
    # بررسی دسترسی کاربر
    user_permissions = UserPermission.objects.filter(
        user=user,
        view_name=view_name
    ).first()
    if user_permissions:
        user_permission_values = {
            field.name: getattr(user_permissions, field.name)
            for field in UserPermission._meta.fields
            if field.name.startswith("can_")
        }
        logger.debug(f"user permissions found: {user_permission_values}")
        permissions.update(user_permission_values)

    logger.debug(f"Final permissions for user {user.username} and view {view_name}: {permissions}")

    return permissions


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
            if not permissions.get("can_view", False):
                raise PermissionDenied("شما اجازه دسترسی به این بخش را ندارید.")
            return original_dispatch(self, *args, **kwargs)

        cls.dispatch = new_dispatch
        return cls

    return decorator