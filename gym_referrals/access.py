"""Bridge between gym_referrals and the central dynamic permissions app.

The permissions app (PartPermission/SectionPermission/PositionPermission/
UnitGroupPermission/UserPermission) stores grants per ``view_name`` string and
is managed through the ``permissions:manage_access`` UI. This module exposes
the gym view names that participate in that system and the decorator that
enforces them.

Access is granted when ANY of the following holds:

1. the user is a superuser;
2. the user holds at least one Django model permission of this app
   (existing administrator/operator roles keep working unchanged);
3. a dynamic grant for the requested view name exists in the permissions app.

Anonymous users are handled by ``login_required`` which always wraps this
decorator. The public QR verification endpoint stays intentionally public and
the redeem endpoint keeps its GymOperator mapping as its authorization.
"""

from functools import wraps

from django.core.exceptions import PermissionDenied

from permissions.utils import check_permission

DENIED_MESSAGE = "شما اجازه دسترسی به این بخش را ندارند."


def get_operator_gyms(user):
    """Gyms the user actively operates via an active GymOperator mapping."""
    if user is None or not user.is_authenticated:
        return []
    from .models import Gym
    if user.is_superuser:
        return list(Gym.objects.filter(is_active=True))
    return list(
        Gym.objects.filter(
            operators__user=user, operators__is_active=True, is_active=True,
        ).distinct()
    )


def has_gym_admin_access(user):
    """True for superusers or holders of any gym_referrals model permission."""
    return user.is_superuser or user.has_module_perms("gym_referrals")


def gym_access_required(view_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not (has_gym_admin_access(user) or any(check_permission(user, view_name).values())):
                raise PermissionDenied(DENIED_MESSAGE)
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def gym_portal_access_required(view_func):
    """Require at least one active GymOperator mapping (role = gym operator).

    Users with gym admin rights (superuser OR any gym_referrals model
    permission) are also allowed, which keeps administrators able to preview
    the portal.
    """

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied(DENIED_MESSAGE)
        if not (has_gym_admin_access(user) or get_operator_gyms(user)):
            raise PermissionDenied(DENIED_MESSAGE)
        return view_func(request, *args, **kwargs)

    return _wrapped
