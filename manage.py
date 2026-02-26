#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import weakref
from types import ModuleType


def main():
    """Run administrative tasks."""

    # ==================== START OF FINAL AUTORELOAD HOTFIX ====================
    # این وصله باید اینجا باشد تا هم در فرآیند والد (reloader) و هم در فرآیند
    # فرزند (server) اجرا شود و مشکل را به طور کامل حل کند.
    try:
        from django.utils import autoreload

        # تابع اصلی جنگو را نگه می‌داریم
        original_iter = autoreload.iter_all_python_module_files

        def safe_iter_all_python_module_files():
            """
            یک نسخه امن از تابع جنگو که قبل از اجرا، لیست فایل‌های خطا
            (_error_files) را از هر آبجکت غیرقابل هشی پاکسازی می‌کند.
            """
            # نسخه بازنویسی‌شده iter_all_python_module_files:
            # 1) ماژول‌ها را مثل خود جنگو جمع می‌کند
            # 2) _error_files را قبل از frozenset از آیتم‌های غیرقابل hash پاک می‌کند
            keys = sorted(sys.modules)
            modules = tuple(
                m
                for m in map(sys.modules.__getitem__, keys)
                if not isinstance(m, weakref.ProxyTypes) and isinstance(m, ModuleType)
            )

            safe_error_files = []
            for item in getattr(autoreload, '_error_files', []):
                try:
                    hash(item)
                except TypeError:
                    continue
                safe_error_files.append(item)

            return autoreload.iter_modules_and_files(modules, frozenset(safe_error_files))

        # تابع امن خود را جایگزین تابع اصلی جنگو می‌کنیم
        autoreload.iter_all_python_module_files = safe_iter_all_python_module_files

    except (ImportError, Exception):
        # اگر در محیطی غیر از runserver باشیم، این کد اجرا نمی‌شود و مشکلی نیست
        pass
    # ===================== END OF FINAL AUTORELOAD HOTFIX =====================

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.development')  # مسیر را در صورت نیاز اصلاح کنید
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
