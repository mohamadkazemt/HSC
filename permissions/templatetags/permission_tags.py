# permissions/templatetags/permission_tags.py
from django import template
from ..utils import check_permission
import logging

register = template.Library()
logger = logging.getLogger(__name__)

@register.filter(name='has_permission')
def has_permission(user, view_name):
    logger.debug(f"has_permission tag called for user: {user.username}, view: {view_name}")
    permissions = check_permission(user, view_name)
    logger.debug(f"check_permission returned permissions: {permissions}")
    return any(permissions.values())


@register.filter(name='check_permission')
def check_permission_filter(user, view_name):
    """Template filter alias so templates can use `user|check_permission:'view_name'`.

    Returns True if any permission flag is set for the view_name for the given user.
    """
    try:
        permissions = check_permission(user, view_name)
        return any(permissions.values())
    except Exception as e:
        logger.error(f"Error in check_permission filter: {e}")
        return False