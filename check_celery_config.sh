#!/bin/bash

# بررسی تنظیمات Celery
# Usage: sudo bash check_celery_config.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/var/www/HSC"
VENV_DIR="$PROJECT_DIR/venv"

echo "========================================="
echo "بررسی تنظیمات Celery"
echo "========================================="
echo ""

cd "$PROJECT_DIR"

echo "1. بررسی تنظیمات Celery از Django:"
echo "----------------------------------------"
sudo -u hsc_admin env DJANGO_SETTINGS_MODULE=HSCprojects.settings.production "$VENV_DIR/bin/python" manage.py shell -c "
import os
import django
django.setup()

from django.conf import settings
from HSCprojects.celery import app

print('تنظیمات Django:')
print(f'  DJANGO_SETTINGS_MODULE: {os.environ.get(\"DJANGO_SETTINGS_MODULE\")}')
print(f'  CELERY_BROKER_URL: {getattr(settings, \"CELERY_BROKER_URL\", \"NOT SET\")}')
print(f'  CELERY_RESULT_BACKEND: {getattr(settings, \"CELERY_RESULT_BACKEND\", \"NOT SET\")}')
print()
print('تنظیمات Celery App:')
print(f'  app.broker_url: {app.conf.broker_url}')
print(f'  app.result_backend: {app.conf.result_backend}')
print(f'  app.timezone: {app.conf.timezone}')
print()
print('تست اتصال:')
try:
    inspect = app.control.inspect()
    stats = inspect.stats()
    if stats:
        print('  ✓ Worker به Redis متصل است')
        print(f'  Worker count: {len(stats)}')
    else:
        print('  ✗ Worker فعالی یافت نشد')
except Exception as e:
    print(f'  ✗ خطا: {str(e)[:200]}')
" 2>&1

echo ""
echo "========================================="
echo "بررسی کامل شد"
echo "========================================="

