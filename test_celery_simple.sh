#!/bin/bash

# تست ساده و پایدار تسک‌های Celery
# Usage: sudo bash test_celery_simple.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================="
echo "تست تسک‌های Celery"
echo "========================================="
echo ""

PROJECT_DIR="/var/www/HSC"
VENV_DIR="$PROJECT_DIR/venv"
ERRORS=0

# Function to check and report
check() {
    local name=$1
    local command=$2
    echo -n "بررسی $name... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        ((ERRORS++))
        return 1
    fi
}

# 1. Check services
echo "1. بررسی سرویس‌ها:"
check "Celery Worker" "systemctl is-active celery-worker"
check "Celery Beat" "systemctl is-active celery-beat"
echo ""

# 2. Check Redis
echo "2. بررسی Redis:"
check "Redis Service" "systemctl is-active redis-server || systemctl is-active redis"
check "Redis Connection" "redis-cli -h localhost -p 6379 ping"
echo ""

# 3. Check database
echo "3. بررسی دیتابیس:"
if [ -d "$VENV_DIR" ] && [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR" 2>/dev/null || {
        echo -e "${RED}✗${NC} نمی‌توان به دایرکتوری پروژه دسترسی پیدا کرد"
        ((ERRORS++))
    }
    
    if [ $? -eq 0 ]; then
        check "Database Connection" "sudo -u hsc_admin \"$VENV_DIR/bin/python\" manage.py check --database default"
    fi
else
    echo -e "${RED}✗${NC} Virtual environment یا پروژه یافت نشد"
    ((ERRORS++))
fi
echo ""

# 4. Check failed tasks
echo "4. بررسی تسک‌های Fail شده:"
if [ -d "$VENV_DIR" ] && [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR" 2>/dev/null
    failed_count=$(sudo -u hsc_admin "$VENV_DIR/bin/python" manage.py shell -c "
from django_celery_results.models import TaskResult
from django.utils import timezone
from datetime import timedelta
try:
    count = TaskResult.objects.filter(
        status='FAILURE',
        date_done__gte=timezone.now() - timedelta(hours=24)
    ).count()
    print(count)
except:
    print('ERROR')
" 2>/dev/null || echo "ERROR")
    
    if [ "$failed_count" = "ERROR" ]; then
        echo -e "  ${RED}✗${NC} خطا در بررسی تسک‌ها"
        ((ERRORS++))
    elif [ "$failed_count" -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} هیچ تسک Fail شده‌ای در 24 ساعت گذشته"
    else
        echo -e "  ${RED}✗${NC} $failed_count تسک Fail شده در 24 ساعت گذشته"
        ((ERRORS++))
    fi
else
    echo -e "  ${RED}✗${NC} Virtual environment یافت نشد"
    ((ERRORS++))
fi
echo ""

# 5. Check Celery connection
echo "5. بررسی اتصال Celery:"
if systemctl is-active --quiet celery-worker && [ -d "$VENV_DIR" ]; then
    cd "$PROJECT_DIR" 2>/dev/null
    # Use production settings
    celery_check=$(sudo -u hsc_admin env DJANGO_SETTINGS_MODULE=HSCprojects.settings.production "$VENV_DIR/bin/celery" -A HSCprojects inspect ping 2>/dev/null | grep -q "pong" && echo "OK" || echo "FAIL")
    
    if [ "$celery_check" = "OK" ]; then
        echo -e "  ${GREEN}✓${NC} Celery Worker به Redis متصل است"
    else
        echo -e "  ${YELLOW}⚠${NC} Celery Worker به Redis متصل نیست (ممکن است هشدار DuplicateNodename باشد)"
        # Don't count as error if it's just duplicate nodename
        if ! sudo -u hsc_admin env DJANGO_SETTINGS_MODULE=HSCprojects.settings.production "$VENV_DIR/bin/celery" -A HSCprojects inspect ping 2>&1 | grep -q "DuplicateNodename"; then
            ((ERRORS++))
        fi
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Worker فعال نیست - نمی‌توان تست کرد"
fi
echo ""

# Summary
echo "========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ همه چیز به درستی کار می‌کند!${NC}"
    exit 0
else
    echo -e "${RED}✗ $ERRORS مشکل یافت شد${NC}"
    exit 1
fi

