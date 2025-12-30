#!/bin/bash

# Quick Celery Test - تست سریع تسک‌های Celery
# Usage: sudo bash quick_celery_test.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="/var/www/HSC"
VENV_DIR="$PROJECT_DIR/venv"

echo "========================================="
echo "تست سریع Celery Tasks"
echo "========================================="
echo ""

# 1. Check services
echo "1. بررسی سرویس‌ها..."
if systemctl is-active --quiet celery-worker; then
    echo -e "${GREEN}✓ Celery Worker فعال${NC}"
else
    echo -e "${RED}✗ Celery Worker غیرفعال${NC}"
    exit 1
fi

if systemctl is-active --quiet celery-beat; then
    echo -e "${GREEN}✓ Celery Beat فعال${NC}"
else
    echo -e "${RED}✗ Celery Beat غیرفعال${NC}"
    exit 1
fi

# 2. Check Redis
echo ""
echo "2. بررسی Redis..."
if redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis در دسترس${NC}"
else
    echo -e "${RED}✗ Redis در دسترس نیست${NC}"
    exit 1
fi

# 3. Check database connection
echo ""
echo "3. بررسی دیتابیس..."
cd "$PROJECT_DIR"
if sudo -u hsc_admin "$VENV_DIR/bin/python" manage.py check --database default > /dev/null 2>&1; then
    echo -e "${GREEN}✓ دیتابیس در دسترس${NC}"
else
    echo -e "${RED}✗ دیتابیس در دسترس نیست${NC}"
    exit 1
fi

# 4. Check failed tasks
echo ""
echo "4. بررسی تسک‌های Fail شده..."
failed_count=$(sudo -u hsc_admin "$VENV_DIR/bin/python" manage.py shell -c "
from django_celery_results.models import TaskResult
from django.utils import timezone
from datetime import timedelta
count = TaskResult.objects.filter(
    status='FAILURE',
    date_done__gte=timezone.now() - timedelta(hours=24)
).count()
print(count)
" 2>/dev/null || echo "0")

if [ "$failed_count" -eq 0 ]; then
    echo -e "${GREEN}✓ هیچ تسک Fail شده‌ای در 24 ساعت گذشته${NC}"
else
    echo -e "${RED}✗ $failed_count تسک Fail شده در 24 ساعت گذشته${NC}"
fi

# 5. Check Celery connection
echo ""
echo "5. بررسی اتصال Celery به Redis..."
if sudo -u hsc_admin "$VENV_DIR/bin/celery" -A HSCprojects inspect ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Celery Worker به Redis متصل است${NC}"
else
    echo -e "${RED}✗ Celery Worker به Redis متصل نیست${NC}"
fi

echo ""
echo "========================================="
echo -e "${GREEN}تست کامل شد${NC}"
echo "========================================="

