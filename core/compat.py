"""Compatibility shims for interpreter/framework combinations outside
official support matrices. Each fix mirrors an upstream Django commit and is
skipped automatically once the installed Django already contains it."""

import inspect
import sys
from copy import copy

import django


def apply_django_context_copy_fix():
    """Backport the upstream fix for copying template contexts on Python 3.14+.

    Django versions without official Python 3.14 support implement
    ``BaseContext.__copy__`` with ``copy(super())``; Python 3.14 super
    proxies no longer tolerate that pattern, so every ``RequestContext``
    copy (e.g. inside the Django test client) crashes with
    ``AttributeError: 'super' object has no attribute 'dicts'``.
    The replacement below matches the current upstream implementation.
    """
    if sys.version_info < (3, 14):
        return False
    from django.template.context import BaseContext

    try:
        needs_fix = "copy(super())" in inspect.getsource(BaseContext.__copy__)
    except (OSError, TypeError):
        needs_fix = True
    if not needs_fix:
        return False

    def __copy__(self):
        duplicate = BaseContext()
        duplicate.__class__ = self.__class__
        duplicate.__dict__ = copy(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = __copy__
    return True
