#!/bin/bash

# تست Debug - با خروجی کامل برای عیب‌یابی
# Usage: sudo bash test_celery_debug.sh

set -x  # نمایش تمام دستورات

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================="
echo "تست Debug تسک‌های Celery"
echo "========================================="
echo ""

PROJECT_DIR="/var/www/HSC"
VENV_DIR="$PROJECT_DIR/venv"

# 1. Check services
echo "1. بررسی سرویس‌ها:"
echo "----------------------------------------"
systemctl status celery-worker --no-pager -l | head -10
echo ""
systemctl status celery-beat --no-pager -l | head -10
echo ""

# 2. Check processes
echo "2. بررسی پروسه‌ها:"
echo "----------------------------------------"
ps aux | grep -E "celery|worker|beat" | grep -v grep
echo ""

# 3. Check Redis
echo "3. بررسی Redis:"
echo "----------------------------------------"
redis-cli -h localhost -p 6379 ping
redis-cli -h localhost -p 6379 info server | head -5
echo ""

# 4. Check project directory
echo "4. بررسی دایرکتوری پروژه:"
echo "----------------------------------------"
ls -la "$PROJECT_DIR" 2>&1 | head -5
echo ""

# 5. Check virtual environment
echo "5. بررسی Virtual Environment:"
echo "----------------------------------------"
if [ -d "$VENV_DIR" ]; then
    echo "✓ Virtual environment موجود است"
    ls -la "$VENV_DIR/bin" | grep -E "python|celery" | head -5
else
    echo "✗ Virtual environment یافت نشد"
fi
echo ""

# 6. Try Django check
echo "6. تست Django:"
echo "----------------------------------------"
if [ -d "$VENV_DIR" ] && [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR"
    sudo -u hsc_admin "$VENV_DIR/bin/python" manage.py check --database default 2>&1
    echo ""
    
    # Try to import celery
    echo "7. تست Import Celery:"
    echo "----------------------------------------"
    sudo -u hsc_admin "$VENV_DIR/bin/python" -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
try:
    from HSCprojects.celery import app
    print('✓ Celery app import شد')
    print(f'  Broker: {app.conf.broker_url}')
    print(f'  Backend: {app.conf.result_backend}')
except Exception as e:
    print(f'✗ خطا در import: {e}')
    import traceback
    traceback.print_exc()
" 2>&1
else
    echo "✗ Virtual environment یا پروژه یافت نشد"
fi
echo ""

# 7. Check Celery inspect
echo "8. تست Celery Inspect:"
echo "----------------------------------------"
if [ -d "$VENV_DIR" ] && systemctl is-active --quiet celery-worker; then
    cd "$PROJECT_DIR"
    sudo -u hsc_admin "$VENV_DIR/bin/celery" -A HSCprojects inspect ping 2>&1
    echo ""
    sudo -u hsc_admin "$VENV_DIR/bin/celery" -A HSCprojects inspect active 2>&1 | head -10
else
    echo "Worker فعال نیست"
fi
echo ""

echo "========================================="
echo "تست Debug کامل شد"
echo "========================================="

