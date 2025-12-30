#!/bin/bash

# اسکریپت برای رفع مشکل اتصال Celery به Redis
# Usage: sudo bash fix_celery_connection.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/var/www/HSC"
VENV_DIR="$PROJECT_DIR/venv"

echo "========================================="
echo "رفع مشکل اتصال Celery به Redis"
echo "========================================="
echo ""

cd "$PROJECT_DIR"

# 1. بررسی تنظیمات فعلی
echo "1. بررسی تنظیمات فعلی Celery:"
echo "----------------------------------------"
sudo -u hsc_admin "$VENV_DIR/bin/python" manage.py shell -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.production')
import django
django.setup()

from django.conf import settings
from HSCprojects.celery import app

print('تنظیمات Django:')
print(f'  CELERY_BROKER_URL: {getattr(settings, \"CELERY_BROKER_URL\", \"NOT SET\")}')
print(f'  CELERY_RESULT_BACKEND: {getattr(settings, \"CELERY_RESULT_BACKEND\", \"NOT SET\")}')
print()
print('تنظیمات Celery App:')
print(f'  app.broker_url: {app.conf.broker_url}')
print(f'  app.result_backend: {app.conf.result_backend}')
" 2>&1

echo ""
echo "2. بررسی فایل service:"
echo "----------------------------------------"
if [ -f "/etc/systemd/system/celery-worker.service" ]; then
    echo "محتوای celery-worker.service:"
    grep -E "DJANGO_SETTINGS_MODULE|Environment" /etc/systemd/system/celery-worker.service || echo "تنظیمات Environment یافت نشد"
else
    echo "✗ فایل service یافت نشد"
fi

echo ""
echo "3. راه‌حل‌های پیشنهادی:"
echo "----------------------------------------"
echo "اگر Broker و Backend None هستند:"
echo "  1. بررسی کنید که DJANGO_SETTINGS_MODULE در service file درست تنظیم شده باشد"
echo "  2. Worker را restart کنید:"
echo "     sudo systemctl restart celery-worker celery-beat"
echo ""
echo "اگر هنوز مشکل دارید:"
echo "  1. بررسی لاگ Worker:"
echo "     sudo journalctl -u celery-worker -n 50"
echo "  2. بررسی اتصال Redis:"
echo "     redis-cli ping"
echo "  3. تست دستی Celery:"
echo "     sudo -u hsc_admin $VENV_DIR/bin/celery -A HSCprojects inspect ping"
echo ""

