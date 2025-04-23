from django.contrib.auth.decorators import permission_required, user_passes_test
from functools import wraps

def in_operations_group(user):
    """بررسی عضویت کاربر در گروه عملیات"""
    return user.groups.filter(name='operations').exists()

def operations_required(view_func):
    """دکوراتور برای محدود کردن دسترسی به اعضای گروه عملیات"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not in_operations_group(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("شما دسترسی به این بخش را ندارید.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view