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