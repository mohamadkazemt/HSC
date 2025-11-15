#!/bin/bash

# اسکریپت اعمال تنظیمات سرور برای حل مشکل آپلود فیش‌های حقوقی

echo "=========================================="
echo "اعمال تنظیمات سرور برای HSC"
echo "=========================================="

# رنگ‌ها
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ۱. بررسی دسترسی root
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}لطفاً با دسترسی root اجرا کنید (sudo)${NC}"
   exit 1
fi

echo -e "\n${YELLOW}[1/5] بررسی فایل‌های Nginx...${NC}"

# بررسی وجود فایل کانفیگ nginx
NGINX_CONFIG="/etc/nginx/sites-available/miepcoj.ir"
if [ ! -f "$NGINX_CONFIG" ]; then
    echo -e "${RED}فایل کانفیگ $NGINX_CONFIG یافت نشد!${NC}"
    echo "لطفاً مسیر صحیح را وارد کنید:"
    read -p "مسیر فایل کانفیگ nginx: " NGINX_CONFIG
fi

echo -e "${GREEN}فایل کانفیگ یافت شد: $NGINX_CONFIG${NC}"

# پشتیبان‌گیری از فایل قبلی
echo -e "\n${YELLOW}[2/5] پشتیبان‌گیری از تنظیمات فعلی...${NC}"
cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}پشتیبان ذخیره شد${NC}"

# اعمال تنظیمات جدید
echo -e "\n${YELLOW}[3/5] آیا می‌خواهید فایل کانفیگ جدید را جایگزین کنید؟${NC}"
echo "فایل جدید: nginx_config_updated.conf"
read -p "بله (y) / خیر (n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "nginx_config_updated.conf" ]; then
        cp nginx_config_updated.conf "$NGINX_CONFIG"
        echo -e "${GREEN}فایل کانفیگ به‌روزرسانی شد${NC}"
    else
        echo -e "${RED}فایل nginx_config_updated.conf یافت نشد!${NC}"
        exit 1
    fi
fi

# تست کانفیگ nginx
echo -e "\n${YELLOW}[4/5] تست تنظیمات Nginx...${NC}"
nginx -t
if [ $? -eq 0 ]; then
    echo -e "${GREEN}تنظیمات Nginx صحیح است${NC}"
else
    echo -e "${RED}خطا در تنظیمات Nginx! تغییرات اعمال نمی‌شود.${NC}"
    echo "بازگردانی از پشتیبان..."
    cp "${NGINX_CONFIG}.backup."* "$NGINX_CONFIG"
    exit 1
fi

# ری‌استارت nginx
echo -e "\n${YELLOW}آیا می‌خواهید Nginx را restart کنید؟${NC}"
read -p "بله (y) / خیر (n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl reload nginx
    echo -e "${GREEN}Nginx reload شد${NC}"
fi

# تنظیمات Gunicorn
echo -e "\n${YELLOW}[5/5] بررسی تنظیمات Gunicorn...${NC}"

GUNICORN_SERVICE="/etc/systemd/system/gunicorn.service"
if [ -f "$GUNICORN_SERVICE" ]; then
    echo -e "${GREEN}فایل سرویس Gunicorn یافت شد${NC}"
    
    # بررسی timeout
    if grep -q "timeout 300" "$GUNICORN_SERVICE"; then
        echo -e "${GREEN}Timeout در Gunicorn تنظیم شده است${NC}"
    else
        echo -e "${YELLOW}⚠️  Timeout در Gunicorn تنظیم نشده است${NC}"
        echo "برای تنظیم دستی:"
        echo "  sudo nano $GUNICORN_SERVICE"
        echo "  در بخش ExecStart اضافه کنید: --timeout 300 --workers 4"
        echo "  سپس: sudo systemctl daemon-reload && sudo systemctl restart gunicorn"
    fi
else
    echo -e "${YELLOW}⚠️  فایل سرویس Gunicorn یافت نشد${NC}"
    echo "اگر از روش دیگری استفاده می‌کنید، timeout را به 300 افزایش دهید"
fi

# خلاصه
echo -e "\n=========================================="
echo -e "${GREEN}تنظیمات با موفقیت اعمال شد!${NC}"
echo "=========================================="
echo ""
echo "تغییرات اعمال شده:"
echo "  ✓ client_max_body_size: 100M"
echo "  ✓ proxy timeouts: 300 seconds"
echo "  ✓ buffer sizes: بهینه شده"
echo ""
echo "لطفاً سایت را تست کنید:"
echo "  1. وارد صفحه مدیریت فیش حقوقی شوید"
echo "  2. ابتدا 50 فایل آپلود کنید"
echo "  3. در صورت موفقیت، 100-150 فایل آپلود کنید"
echo ""
echo "در صورت بروز مشکل:"
echo "  - لاگ‌های Nginx: tail -f /var/log/nginx/miepcoj.ir.error.log"
echo "  - لاگ‌های Gunicorn: journalctl -u gunicorn -f"
echo "  - لاگ‌های Django: tail -f /var/www/HSC/logs/errors.log"
echo ""
