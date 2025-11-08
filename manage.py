#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Suppress GLib warnings about incomplete UWP app registrations on Windows.
# This warning originates from the GTK stack pulled in by WeasyPrint. Setting
# the following env var disables UWP app registration probing in GLib and keeps
# the console output clean without affecting functionality.
os.environ.setdefault('LIBGLIB_DISABLE_UWP_APP_REGISTRATION', '1')


def main():
    """Run administrative tasks."""
    # تشخیص محیط اجرا
    if os.environ.get('DJANGO_ENV') == 'production':
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.production')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.development')
    
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
