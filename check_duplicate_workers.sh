#!/bin/bash

# بررسی Workerهای تکراری
# Usage: sudo bash check_duplicate_workers.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/var/www/HSC"
VENV_DIR="$PROJECT_DIR/venv"

echo "========================================="
echo "بررسی Workerهای تکراری"
echo "========================================="
echo ""

cd "$PROJECT_DIR"

echo "1. بررسی Workerهای فعال:"
echo "----------------------------------------"
sudo -u hsc_admin env DJANGO_SETTINGS_MODULE=HSCprojects.settings.production "$VENV_DIR/bin/celery" -A HSCprojects inspect active 2>&1 | head -20

echo ""
echo "2. بررسی Workerهای ثبت شده:"
echo "----------------------------------------"
sudo -u hsc_admin env DJANGO_SETTINGS_MODULE=HSCprojects.settings.production "$VENV_DIR/bin/celery" -A HSCprojects inspect stats 2>&1 | head -30

echo ""
echo "3. بررسی پروسه‌های Celery:"
echo "----------------------------------------"
ps aux | grep -E "celery.*worker" | grep -v grep

echo ""
echo "4. بررسی سرویس‌های Systemd:"
echo "----------------------------------------"
systemctl status celery-worker --no-pager -l | head -15

echo ""
echo "========================================="
echo "راه‌حل:"
echo "========================================="
echo "اگر Workerهای تکراری دارید:"
echo "1. تمام Workerها را متوقف کنید:"
echo "   sudo systemctl stop celery-worker"
echo ""
echo "2. پروسه‌های باقی‌مانده را kill کنید:"
echo "   sudo pkill -f 'celery.*worker'"
echo ""
echo "3. Worker را دوباره راه‌اندازی کنید:"
echo "   sudo systemctl start celery-worker"
echo ""
echo "4. برای جلوگیری از تکرار، در service file از -n استفاده کنید:"
echo "   -n celery@%h-%i"
echo "========================================="

