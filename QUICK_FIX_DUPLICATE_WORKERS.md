# رفع سریع مشکل Workerهای تکراری

## مشکل شناسایی شده

یک Worker اضافی در حال اجرا است که از service file نیست:
- PID: 1294582
- مسیر لاگ: `/var/log/celery/worker.log` (نه `/var/www/HSC/logs/celery-worker.log`)
- بدون `--max-tasks-per-child`

## راه‌حل سریع

### مرحله 1: Kill کردن Worker اضافی

```bash
# پیدا کردن Worker اضافی
ps aux | grep "celery.*HSCprojects.*worker" | grep -v grep

# Kill کردن Worker اضافی (PID 1294582)
sudo kill -TERM 1294582

# اگر kill نشد، force kill
sudo kill -9 1294582
```

یا استفاده از اسکریپت:
```bash
sudo bash fix_duplicate_workers.sh
```

### مرحله 2: بررسی Service File

```bash
# بررسی service file
cat /etc/systemd/system/celery-worker.service | grep ExecStart
```

باید این خط را ببینید:
```
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects worker \
    --pool=prefork \
    --concurrency=8 \
    --max-tasks-per-child=1000 \
    --loglevel=info \
    --logfile=/var/www/HSC/logs/celery-worker.log \
    --hostname=worker@%h
```

اگر `--hostname=worker@%h` نیست، اضافه کنید.

### مرحله 3: به‌روزرسانی Service File

```bash
# کپی فایل جدید
sudo cp /var/www/HSC/documentation/celery-worker.service /etc/systemd/system/celery-worker.service

# یا ویرایش دستی
sudo nano /etc/systemd/system/celery-worker.service
```

اضافه کردن `--hostname=worker@%h` به خط ExecStart.

### مرحله 4: Reload و Restart

```bash
sudo systemctl daemon-reload
sudo systemctl restart celery-worker
sudo systemctl status celery-worker
```

### مرحله 5: تست

```bash
sudo bash test_celery_simple.sh
sudo bash check_duplicate_workers.sh
```

## دستورات یکجا

```bash
# 1. Kill Worker اضافی
sudo kill -TERM 1294582 2>/dev/null || true
sleep 2
sudo kill -9 1294582 2>/dev/null || true

# 2. بررسی Workerهای باقی‌مانده
ps aux | grep "celery.*HSCprojects.*worker" | grep -v grep

# 3. به‌روزرسانی service file (اگر نیاز است)
sudo cp /var/www/HSC/documentation/celery-worker.service /etc/systemd/system/celery-worker.service

# 4. Reload و Restart
sudo systemctl daemon-reload
sudo systemctl restart celery-worker

# 5. تست
sudo bash test_celery_simple.sh
```

## بررسی نهایی

```bash
# بررسی Workerهای فعال
sudo -u hsc_admin env DJANGO_SETTINGS_MODULE=HSCprojects.settings.production /var/www/HSC/venv/bin/celery -A HSCprojects inspect ping

# باید فقط یک Worker پاسخ دهد (بدون هشدار DuplicateNodename)
```

