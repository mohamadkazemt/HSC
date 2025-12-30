#!/bin/bash

# نمایش تسک‌های Fail شده
# Usage: sudo bash view_failed_tasks.sh [hours]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/var/www/HSC"
VENV_DIR="$PROJECT_DIR/venv"
HOURS=${1:-24}  # پیش‌فرض 24 ساعت

echo "========================================="
echo "تسک‌های Fail شده (آخرین $HOURS ساعت)"
echo "========================================="
echo ""

cd "$PROJECT_DIR"

# Get failed tasks
sudo -u hsc_admin "$VENV_DIR/bin/python" manage.py shell << EOF
from django_celery_results.models import TaskResult
from django.utils import timezone
from datetime import timedelta
import json

failed_tasks = TaskResult.objects.filter(
    status='FAILURE',
    date_done__gte=timezone.now() - timedelta(hours=$HOURS)
).order_by('-date_done')[:50]

print(f"تعداد تسک‌های Fail شده: {failed_tasks.count()}\n")

if failed_tasks.exists():
    for i, task in enumerate(failed_tasks, 1):
        print(f"{i}. {task.task_name}")
        print(f"   Task ID: {task.task_id}")
        print(f"   زمان: {task.date_done}")
        if task.traceback:
            # نمایش خطای اول
            error_line = task.traceback.split('\n')[-2] if '\n' in task.traceback else task.traceback
            print(f"   خطا: {error_line[:100]}...")
        print()
else:
    print("✓ هیچ تسک Fail شده‌ای یافت نشد")
EOF

echo ""
echo "========================================="
echo "برای مشاهده جزئیات کامل یک تسک:"
echo "sudo -u hsc_admin $VENV_DIR/bin/python manage.py shell"
echo ">>> from django_celery_results.models import TaskResult"
echo ">>> task = TaskResult.objects.get(task_id='TASK_ID')"
echo ">>> print(task.traceback)"
echo "========================================="

