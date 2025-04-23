# permissions/context_processors.py
from .utils import check_permission

def permission_context(request):
    """
    Adds the check_permission function to the template context.
    """
    return {'check_permission': check_permission}

def request(request):
    return {'request': request}