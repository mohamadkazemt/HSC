#!/bin/bash

# به‌روزرسانی service file برای اضافه کردن hostname
# Usage: sudo bash update_service_file.sh [service-name]
# service-name می‌تواند باشد: celery-worker, celery-beat, rubika-bot, یا all

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_DIR="/var/www/HSC"
SERVICE_NAME=${1:-celery-worker}

# Map service names to files
case "$SERVICE_NAME" in
    celery-worker)
        SERVICE_FILE="/etc/systemd/system/celery-worker.service"
        SOURCE_FILE="$PROJECT_DIR/celery-worker.service"
        ;;
    celery-beat)
        SERVICE_FILE="/etc/systemd/system/celery-beat.service"
        SOURCE_FILE="$PROJECT_DIR/celery-beat.service"
        ;;
    rubika-bot)
        SERVICE_FILE="/etc/systemd/system/rubika-bot.service"
        SOURCE_FILE="$PROJECT_DIR/rubika-bot.service"
        ;;
    all)
        # Update all services
        bash "$0" celery-worker
        bash "$0" celery-beat
        bash "$0" rubika-bot
        exit 0
        ;;
    *)
        echo "Usage: $0 [celery-worker|celery-beat|rubika-bot|all]"
        exit 1
        ;;
esac

echo "========================================="
echo "به‌روزرسانی Service File"
echo "========================================="
echo ""

# بررسی وجود فایل منبع
if [ -z "$SOURCE_FILE" ] || [ ! -f "$SOURCE_FILE" ]; then
    echo -e "${RED}✗ فایل منبع یافت نشد${NC}"
    echo "   جستجو در:"
    echo "   - $PROJECT_DIR/celery-worker.service"
    echo "   - $PROJECT_DIR/documentation/celery-worker.service"
    echo ""
    echo "   لطفاً فایل celery-worker.service را در root directory پروژه قرار دهید"
    exit 1
fi

echo "   استفاده از: $SOURCE_FILE"

# بررسی hostname در فایل منبع
if ! grep -q "hostname" "$SOURCE_FILE" 2>/dev/null; then
    echo -e "${RED}✗ فایل منبع hostname ندارد${NC}"
    exit 1
fi

echo "1. بررسی فایل فعلی:"
echo "----------------------------------------"
if grep -q "hostname" "$SERVICE_FILE" 2>/dev/null; then
    echo -e "${GREEN}✓ hostname در service file موجود است${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ hostname در service file موجود نیست${NC}"
fi

echo ""
echo "2. کپی فایل به‌روز:"
echo "----------------------------------------"
sudo cp "$SOURCE_FILE" "$SERVICE_FILE"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ فایل کپی شد${NC}"
else
    echo -e "${RED}✗ خطا در کپی فایل${NC}"
    exit 1
fi

echo ""
echo "3. Reload systemd:"
echo "----------------------------------------"
sudo systemctl daemon-reload
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Systemd reload شد${NC}"
else
    echo -e "${RED}✗ خطا در reload${NC}"
    exit 1
fi

echo ""
echo "4. بررسی نهایی:"
echo "----------------------------------------"
if grep -q "hostname" "$SERVICE_FILE" 2>/dev/null; then
    echo -e "${GREEN}✓ hostname در service file تنظیم شد${NC}"
    echo ""
    echo "برای اعمال تغییرات، Worker را restart کنید:"
    echo "  sudo systemctl restart celery-worker"
else
    echo -e "${RED}✗ هنوز hostname تنظیم نشده است${NC}"
    exit 1
fi

echo ""
echo "========================================="
echo "✓ انجام شد"
echo "========================================="

