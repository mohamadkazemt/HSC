#!/bin/bash

# رفع مشکل Workerهای تکراری
# Usage: sudo bash fix_duplicate_workers.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================="
echo "رفع مشکل Workerهای تکراری"
echo "========================================="
echo ""

# 1. پیدا کردن Workerهای اضافی
echo "1. پیدا کردن Workerهای اضافی:"
echo "----------------------------------------"
EXTRA_WORKERS=$(ps aux | grep -E "celery.*HSCprojects.*worker" | grep -v grep | grep -v "celery-worker.service" | awk '{print $2}')

if [ -z "$EXTRA_WORKERS" ]; then
    echo -e "${GREEN}✓ هیچ Worker اضافی یافت نشد${NC}"
else
    echo -e "${YELLOW}⚠ Workerهای اضافی یافت شد:${NC}"
    ps aux | grep -E "celery.*HSCprojects.*worker" | grep -v grep | grep -v "celery-worker.service"
    echo ""
    echo "PIDهای Workerهای اضافی: $EXTRA_WORKERS"
fi

echo ""
echo "2. بررسی Worker از service:"
echo "----------------------------------------"
SERVICE_WORKER=$(systemctl show celery-worker.service -p MainPID --value)
if [ -n "$SERVICE_WORKER" ] && [ "$SERVICE_WORKER" != "0" ]; then
    echo -e "${GREEN}✓ Worker از service: PID $SERVICE_WORKER${NC}"
    ps -p $SERVICE_WORKER -o pid,cmd --no-headers
else
    echo -e "${RED}✗ Worker از service یافت نشد${NC}"
fi

echo ""
echo "3. اقدامات:"
echo "----------------------------------------"

# Kill کردن Workerهای اضافی
if [ -n "$EXTRA_WORKERS" ]; then
    echo "Kill کردن Workerهای اضافی..."
    for pid in $EXTRA_WORKERS; do
        if [ "$pid" != "$SERVICE_WORKER" ]; then
            echo -e "${YELLOW}Killing PID $pid...${NC}"
            kill -TERM $pid 2>/dev/null
            sleep 2
            # اگر هنوز زنده است، force kill
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${RED}Force killing PID $pid...${NC}"
                kill -9 $pid 2>/dev/null
            fi
        fi
    done
    echo -e "${GREEN}✓ Workerهای اضافی kill شدند${NC}"
else
    echo -e "${GREEN}✓ هیچ Worker اضافی برای kill وجود ندارد${NC}"
fi

echo ""
echo "4. بررسی و به‌روزرسانی service file:"
echo "----------------------------------------"
if grep -q "hostname" /etc/systemd/system/celery-worker.service 2>/dev/null; then
    echo -e "${GREEN}✓ hostname در service file تنظیم شده است${NC}"
else
    echo -e "${YELLOW}⚠ hostname در service file تنظیم نشده است${NC}"
    
    # بررسی وجود فایل در documentation
    if [ -f "$PROJECT_DIR/documentation/celery-worker.service" ]; then
        echo "   پیدا کردن فایل به‌روز در documentation..."
        if grep -q "hostname" "$PROJECT_DIR/documentation/celery-worker.service" 2>/dev/null; then
            echo -e "${BLUE}   فایل به‌روز یافت شد. کپی کردن...${NC}"
            read -p "   آیا می‌خواهید service file را به‌روزرسانی کنید? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo cp "$PROJECT_DIR/documentation/celery-worker.service" /etc/systemd/system/celery-worker.service
                echo -e "${GREEN}   ✓ Service file به‌روزرسانی شد${NC}"
                echo "   Reloading systemd..."
                sudo systemctl daemon-reload
                echo -e "${GREEN}   ✓ Systemd reload شد${NC}"
            fi
        else
            echo "   فایل در documentation هم hostname ندارد"
        fi
    else
        echo "   فایل در documentation یافت نشد"
    fi
    echo ""
    echo "   اگر به صورت دستی می‌خواهید اضافه کنید:"
    echo "   sudo nano /etc/systemd/system/celery-worker.service"
    echo "   و این خط را اضافه کنید: --hostname=worker@%h"
fi

echo ""
echo "5. Restart کردن Worker:"
echo "----------------------------------------"
read -p "آیا می‌خواهید Worker را restart کنید? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Restarting celery-worker..."
    systemctl restart celery-worker
    sleep 3
    systemctl status celery-worker --no-pager -l | head -15
fi

echo ""
echo "========================================="
echo "✓ انجام شد"
echo "========================================="

