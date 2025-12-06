#!/bin/bash
# اسکریپت برای گرفتن لاگ‌های خطای Django/Gunicorn

echo "=== آخرین خطاهای Gunicorn ==="
journalctl -u gunicorn -n 200 --no-pager | grep -A 50 "emergency\|ERROR\|Traceback\|Exception"

echo ""
echo "=== لاگ‌های Django (اگر وجود دارد) ==="
if [ -f "/var/log/django/error.log" ]; then
    tail -n 100 /var/log/django/error.log
elif [ -f "/var/www/HSC/logs/error.log" ]; then
    tail -n 100 /var/www/HSC/logs/error.log
else
    echo "فایل لاگ Django پیدا نشد"
fi

echo ""
echo "=== بررسی وضعیت Gunicorn ==="
systemctl status gunicorn --no-pager -l

