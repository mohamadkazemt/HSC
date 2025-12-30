#!/bin/bash

# Advanced Celery Tasks Test Script
# بررسی کامل تسک‌های Celery، Redis و دیتابیس
# Usage: sudo bash test_celery_tasks.sh

# Don't exit on error - we want to continue checking all services
set +e

echo "========================================="
echo "HSC Project - Celery Tasks Comprehensive Test"
echo "بررسی کامل تسک‌های Celery، Redis و دیتابیس"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Project variables
PROJECT_DIR="/var/www/HSC"
VENV_DIR="$PROJECT_DIR/venv"
DJANGO_SETTINGS="HSCprojects.settings.production"

# Test results
PASSED=0
FAILED=0
WARNINGS=0
FAILED_TESTS=()
WARNING_TESTS=()

# Function to log test result
log_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
    FAILED_TESTS+=("$1")
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
    WARNING_TESTS+=("$1")
}

# ============================================
# 1. بررسی سرویس‌های Systemd
# ============================================
echo -e "${BLUE}1. بررسی سرویس‌های Systemd${NC}"
echo "----------------------------------------"

check_service() {
    local service=$1
    local status=$(systemctl is-active "$service" 2>/dev/null || echo "not-found")
    
    if [ "$status" = "active" ]; then
        log_pass "سرویس $service فعال است"
        
        # Check if process is running
        case "$service" in
            celery-worker)
                if pgrep -f "celery.*worker" > /dev/null 2>&1; then
                    log_pass "پروسه Celery Worker در حال اجرا است"
                else
                    log_warning "پروسه Celery Worker یافت نشد (ممکن است در حال راه‌اندازی باشد)"
                fi
                ;;
            celery-beat)
                if pgrep -f "celery.*beat" > /dev/null 2>&1; then
                    log_pass "پروسه Celery Beat در حال اجرا است"
                else
                    log_warning "پروسه Celery Beat یافت نشد (ممکن است در حال راه‌اندازی باشد)"
                fi
                ;;
        esac
    else
        log_fail "سرویس $service فعال نیست (وضعیت: $status)"
    fi
}

check_service "celery-worker"
check_service "celery-beat"
echo ""

# ============================================
# 2. بررسی Redis
# ============================================
echo -e "${BLUE}2. بررسی اتصال Redis${NC}"
echo "----------------------------------------"

# Check Redis service
if systemctl is-active --quiet redis-server || systemctl is-active --quiet redis; then
    log_pass "سرویس Redis فعال است"
else
    log_warning "سرویس Redis یافت نشد (ممکن است با نام دیگری اجرا شود)"
fi

# Test Redis connection
if command -v redis-cli &> /dev/null; then
    if redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
        log_pass "اتصال به Redis برقرار است (localhost:6379)"
        
        # Check Redis databases
        redis_info=$(redis-cli -h localhost -p 6379 info keyspace 2>/dev/null || echo "")
        if [ -n "$redis_info" ]; then
            echo "  اطلاعات Redis Keyspace:"
            echo "$redis_info" | sed 's/^/    /'
        fi
    else
        log_fail "اتصال به Redis برقرار نیست"
    fi
else
    log_warning "redis-cli یافت نشد - نمی‌توان اتصال را تست کرد"
fi

# Test specific Redis databases used by Celery
echo ""
echo "  بررسی دیتابیس‌های Redis:"
for db in 0 1 2; do
    if redis-cli -h localhost -p 6379 -n $db ping > /dev/null 2>&1; then
        key_count=$(redis-cli -h localhost -p 6379 -n $db dbsize 2>/dev/null || echo "0")
        log_pass "Redis DB $db در دسترس است ($key_count کلید)"
    else
        log_fail "Redis DB $db در دسترس نیست"
    fi
done
echo ""

# ============================================
# 3. بررسی دیتابیس Django
# ============================================
echo -e "${BLUE}3. بررسی اتصال دیتابیس Django${NC}"
echo "----------------------------------------"

if [ -d "$VENV_DIR" ]; then
    # Test database connection using Django management command
    cd "$PROJECT_DIR" || {
        log_fail "نمی‌توان به دایرکتوری پروژه دسترسی پیدا کرد"
        echo ""
        exit 1
    }
    if sudo -u hsc_admin "$VENV_DIR/bin/python" manage.py check --database default > /dev/null 2>&1; then
        log_pass "اتصال به دیتابیس Django برقرار است"
        
        # Check if django_celery_results tables exist
        if sudo -u hsc_admin "$VENV_DIR/bin/python" manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'django_celery_results%'\" if 'sqlite' in str(connection.vendor) else \"SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'django_celery_results%'\")
tables = cursor.fetchall()
print('OK' if tables else 'MISSING')
" 2>/dev/null | grep -q "OK"; then
            log_pass "جداول django_celery_results موجود است"
        else
            log_warning "جداول django_celery_results یافت نشد (ممکن است نیاز به migrate باشد)"
        fi
    else
        log_fail "اتصال به دیتابیس Django برقرار نیست"
    fi
else
    log_fail "Virtual environment یافت نشد در $VENV_DIR"
fi
echo ""

# ============================================
# 4. بررسی وضعیت تسک‌های Celery
# ============================================
echo -e "${BLUE}4. بررسی وضعیت تسک‌های Celery${NC}"
echo "----------------------------------------"

if [ -d "$VENV_DIR" ]; then
    cd "$PROJECT_DIR" || {
        log_fail "نمی‌توان به دایرکتوری پروژه دسترسی پیدا کرد"
        echo ""
        exit 1
    }
    
    # Check Celery inspect (requires running worker)
    if systemctl is-active --quiet celery-worker; then
        # Get active tasks
        active_tasks=$(sudo -u hsc_admin "$VENV_DIR/bin/celery" -A HSCprojects inspect active 2>/dev/null | grep -c "task" || echo "0")
        if [ "$active_tasks" -gt 0 ]; then
            log_pass "$active_tasks تسک فعال در حال اجرا است"
        else
            log_pass "هیچ تسک فعالی در حال اجرا نیست (طبیعی است)"
        fi
        
        # Get registered tasks
        registered_tasks=$(sudo -u hsc_admin "$VENV_DIR/bin/celery" -A HSCprojects inspect registered 2>/dev/null | grep -c "\.tasks\." || echo "0")
        if [ "$registered_tasks" -gt 0 ]; then
            log_pass "$registered_tasks تسک ثبت شده در Worker"
        else
            log_warning "هیچ تسکی در Worker ثبت نشده است"
        fi
        
        # Get worker stats
        worker_stats=$(sudo -u hsc_admin "$VENV_DIR/bin/celery" -A HSCprojects inspect stats 2>/dev/null || echo "")
        if [ -n "$worker_stats" ]; then
            echo "  آمار Worker:"
            echo "$worker_stats" | head -20 | sed 's/^/    /'
        fi
    else
        log_fail "Celery Worker فعال نیست - نمی‌توان وضعیت تسک‌ها را بررسی کرد"
    fi
fi
echo ""

# ============================================
# 5. بررسی تسک‌های Fail شده در دیتابیس
# ============================================
echo -e "${BLUE}5. بررسی تسک‌های Fail شده در دیتابیس${NC}"
echo "----------------------------------------"

if [ -d "$VENV_DIR" ]; then
    cd "$PROJECT_DIR" || {
        log_fail "نمی‌توان به دایرکتوری پروژه دسترسی پیدا کرد"
        echo ""
        exit 1
    }
    
    # Check failed tasks from django_celery_results
    failed_tasks=$(sudo -u hsc_admin "$VENV_DIR/bin/python" manage.py shell -c "
from django_celery_results.models import TaskResult
from django.utils import timezone
from datetime import timedelta

# Check failed tasks in last 24 hours
recent_failed = TaskResult.objects.filter(
    status='FAILURE',
    date_done__gte=timezone.now() - timedelta(days=1)
).count()

# Check total failed tasks
total_failed = TaskResult.objects.filter(status='FAILURE').count()

# Check pending tasks (stuck)
pending_tasks = TaskResult.objects.filter(
    status='PENDING',
    date_created__lt=timezone.now() - timedelta(hours=1)
).count()

print(f'{recent_failed}|{total_failed}|{pending_tasks}')
" 2>/dev/null || echo "0|0|0")
    
    recent_failed=$(echo "$failed_tasks" | cut -d'|' -f1)
    total_failed=$(echo "$failed_tasks" | cut -d'|' -f2)
    pending_stuck=$(echo "$failed_tasks" | cut -d'|' -f3)
    
    if [ "$recent_failed" -eq 0 ]; then
        log_pass "هیچ تسک Fail شده‌ای در 24 ساعت گذشته وجود ندارد"
    else
        log_fail "$recent_failed تسک در 24 ساعت گذشته Fail شده است"
        echo "    برای مشاهده جزئیات:"
        echo "    sudo -u hsc_admin $VENV_DIR/bin/python manage.py shell"
        echo "    >>> from django_celery_results.models import TaskResult"
        echo "    >>> TaskResult.objects.filter(status='FAILURE').order_by('-date_done')[:10]"
    fi
    
    if [ "$total_failed" -gt 0 ]; then
        log_warning "مجموع $total_failed تسک Fail شده در دیتابیس وجود دارد"
    fi
    
    if [ "$pending_stuck" -gt 0 ]; then
        log_fail "$pending_stuck تسک PENDING بیش از 1 ساعت است (احتمالاً گیر کرده)"
    else
        log_pass "هیچ تسک PENDING گیر کرده‌ای وجود ندارد"
    fi
else
    log_fail "Virtual environment یافت نشد"
fi
echo ""

# ============================================
# 6. تست اتصال Celery به Redis
# ============================================
echo -e "${BLUE}6. تست اتصال Celery به Redis${NC}"
echo "----------------------------------------"

if [ -d "$VENV_DIR" ] && systemctl is-active --quiet celery-worker; then
    cd "$PROJECT_DIR" || {
        log_fail "نمی‌توان به دایرکتوری پروژه دسترسی پیدا کرد"
        echo ""
        exit 1
    }
    
    # Try to send a test task
    test_result=$(sudo -u hsc_admin "$VENV_DIR/bin/python" manage.py shell -c "
from HSCprojects.celery import app
try:
    # Check broker connection
    inspect = app.control.inspect()
    stats = inspect.stats()
    if stats:
        print('OK')
    else:
        print('NO_WORKERS')
except Exception as e:
    print(f'ERROR: {str(e)}')
" 2>/dev/null || echo "ERROR")
    
    if [ "$test_result" = "OK" ]; then
        log_pass "اتصال Celery Worker به Redis برقرار است"
    elif [ "$test_result" = "NO_WORKERS" ]; then
        log_warning "Worker به Redis متصل است اما Worker فعالی یافت نشد"
    else
        log_fail "اتصال Celery Worker به Redis برقرار نیست: $test_result"
    fi
else
    log_warning "Celery Worker فعال نیست - نمی‌توان اتصال را تست کرد"
fi
echo ""

# ============================================
# 7. بررسی Scheduled Tasks (Beat)
# ============================================
echo -e "${BLUE}7. بررسی Scheduled Tasks (Celery Beat)${NC}"
echo "----------------------------------------"

if [ -d "$VENV_DIR" ] && systemctl is-active --quiet celery-beat; then
    cd "$PROJECT_DIR" || {
        log_fail "نمی‌توان به دایرکتوری پروژه دسترسی پیدا کرد"
        echo ""
        exit 1
    }
    
    # Check beat schedule
    schedule_info=$(sudo -u hsc_admin "$VENV_DIR/bin/python" manage.py shell -c "
from django_celery_beat.models import PeriodicTask
try:
    active_tasks = PeriodicTask.objects.filter(enabled=True).count()
    total_tasks = PeriodicTask.objects.count()
    print(f'{active_tasks}|{total_tasks}')
except Exception as e:
    print(f'ERROR|{str(e)}')
" 2>/dev/null || echo "0|0")
    
    active_scheduled=$(echo "$schedule_info" | cut -d'|' -f1)
    total_scheduled=$(echo "$schedule_info" | cut -d'|' -f2)
    
    if [ "$active_scheduled" -gt 0 ]; then
        log_pass "$active_scheduled تسک زمان‌بندی شده فعال است"
    else
        log_warning "هیچ تسک زمان‌بندی شده فعالی وجود ندارد"
    fi
    
    # Check beat schedule file
    if [ -f "/var/lib/celery/beat-schedule" ] || [ -f "$PROJECT_DIR/celerybeat-schedule" ]; then
        log_pass "فایل Beat Schedule موجود است"
    else
        log_warning "فایل Beat Schedule یافت نشد (ممکن است در اولین اجرا ایجاد شود)"
    fi
else
    log_fail "Celery Beat فعال نیست"
fi
echo ""

# ============================================
# 8. بررسی لاگ‌های خطا
# ============================================
echo -e "${BLUE}8. بررسی لاگ‌های خطای اخیر${NC}"
echo "----------------------------------------"

# Check recent errors in celery-worker logs
worker_errors=$(journalctl -u celery-worker --since "1 hour ago" --no-pager 2>/dev/null | grep -i "error\|exception\|failed\|traceback" 2>/dev/null | wc -l || echo "0")
if [ "$worker_errors" -eq 0 ]; then
    log_pass "هیچ خطایی در لاگ Worker در 1 ساعت گذشته وجود ندارد"
elif [ "$worker_errors" -lt 5 ]; then
    log_warning "$worker_errors خطا در لاگ Worker در 1 ساعت گذشته"
else
    log_fail "$worker_errors خطا در لاگ Worker در 1 ساعت گذشته"
    echo "    برای مشاهده لاگ‌ها:"
    echo "    sudo journalctl -u celery-worker --since '1 hour ago' | grep -i error"
fi

# Check recent errors in celery-beat logs
beat_errors=$(journalctl -u celery-beat --since "1 hour ago" --no-pager 2>/dev/null | grep -i "error\|exception\|failed\|traceback" 2>/dev/null | wc -l || echo "0")
if [ "$beat_errors" -eq 0 ]; then
    log_pass "هیچ خطایی در لاگ Beat در 1 ساعت گذشته وجود ندارد"
elif [ "$beat_errors" -lt 3 ]; then
    log_warning "$beat_errors خطا در لاگ Beat در 1 ساعت گذشته"
else
    log_fail "$beat_errors خطا در لاگ Beat در 1 ساعت گذشته"
fi
echo ""

# ============================================
# خلاصه نتایج
# ============================================
echo "========================================="
echo "خلاصه نتایج / Summary"
echo "========================================="
echo -e "${GREEN}موفق: $PASSED${NC}"
echo -e "${YELLOW}هشدار: $WARNINGS${NC}"
echo -e "${RED}ناموفق: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ همه چیز به درستی کار می‌کند!${NC}"
    echo ""
    exit 0
elif [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}⚠ همه سرویس‌ها فعال هستند اما برخی هشدارها وجود دارد${NC}"
    echo ""
    if [ ${#WARNING_TESTS[@]} -gt 0 ]; then
        echo "هشدارها:"
        for warning in "${WARNING_TESTS[@]}"; do
            echo -e "  ${YELLOW}- $warning${NC}"
        done
    fi
    echo ""
    exit 0
else
    echo -e "${RED}✗ برخی مشکلات وجود دارد${NC}"
    echo ""
    if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
        echo "مشکلات:"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "  ${RED}- $test${NC}"
        done
    fi
    echo ""
    echo "دستورات عیب‌یابی:"
    echo "  sudo systemctl status celery-worker"
    echo "  sudo systemctl status celery-beat"
    echo "  sudo journalctl -u celery-worker -n 100"
    echo "  sudo journalctl -u celery-beat -n 100"
    echo "  redis-cli ping"
    echo ""
    exit 1
fi

