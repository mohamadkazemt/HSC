#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


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
            # بررسی می‌کنیم که آیا لیستی به نام _error_files وجود دارد
            if hasattr(autoreload, '_error_files'):
                # یک لیست جدید فقط با آیتم‌های امن (رشته‌ها و بایت‌ها) می‌سازیم
                autoreload._error_files = [
                    item for item in autoreload._error_files
                    if isinstance(item, (str, bytes))
                ]

            # حالا تابع اصلی و امن‌شده جنگو را فراخوانی می‌کنیم
            return original_iter()

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
