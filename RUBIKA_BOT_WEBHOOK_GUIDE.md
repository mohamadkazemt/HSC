# 🔧 راهنمای رفع مشکل ربات روبیکا (Webhook Mode)

## 🎯 معماری سیستم:

شما از **Webhook Mode** استفاده می‌کنید که سریع‌تر از Polling هست:

```
روبیکا → POST /rubika_bot/webhook/ → Celery Task → RubPyIntegrationService
```

### مشکلی که بود:
- ✅ `run_rubika_bot` در حال اجرا بود
- ❌ اما هیچوقت Client رو Initialize نمی‌کرد
- ❌ پس Handler ها register نمی‌شدند
- ❌ در نتیجه وقتی Celery task میخواست از Service استفاده کنه، Client مقداردهی نشده بود

---

## ✅ راه حل انجام شده:

### 1. Initialize کردن Client در Startup
در `run_rubika_bot.py` اضافه شد:
```python
service._ensure_client_initialized()
```

این باعث می‌شه:
- Client ساخته بشه
- Handler ها register بشن
- Engine آماده کار بشه

### 2. بهبود لاگ‌ها
- لاگ Proxy اضافه شد
- لاگ Client initialization اضافه شد
- پیام‌های بهتر در console

---

## 📋 دستورات اجرا در سرور:

### مرحله 1: آپلود فایل‌ها

```bash
cd /home/miepcoj/web/miepcoj.ir/public_html/HSC

# با git:
git pull origin main

# یا آپلود دستی:
# - rubika_bot/services.py
# - rubika_bot/management/commands/run_rubika_bot.py
```

### مرحله 2: بررسی Celery Worker

ربات روبیکا شما به **Celery Worker** نیاز داره:

```bash
# بررسی وضعیت Celery
sudo systemctl status celery-worker.service

# اگر خاموش بود:
sudo systemctl start celery-worker.service
sudo systemctl enable celery-worker.service
```

### مرحله 3: بررسی Proxy (مهم!)

```bash
python manage.py shell --settings=HSCprojects.settings.production
```

```python
from rubika_bot.models import RubikaBotSettings

settings = RubikaBotSettings.objects.first()
print(f"Proxy enabled: {settings.proxy_enabled}")

# مشکل شما: Proxy نیاز به username/password داشت
# اگر Proxy مشکل داره، خاموشش کن:
settings.proxy_enabled = False
settings.save()
print("✅ Proxy disabled")

exit()
```

### مرحله 4: Restart سرویس‌ها

```bash
# Restart ربات
sudo systemctl restart rubika-bot.service

# Restart Celery (مهم!)
sudo systemctl restart celery-worker.service
sudo systemctl restart celery-beat.service  # اگر داری
```

### مرحله 5: بررسی لاگ‌ها

```bash
# لاگ ربات
sudo journalctl -u rubika-bot.service -f

# لاگ Celery (مهم‌تر!)
sudo journalctl -u celery-worker.service -f
```

---

## 🔍 لاگ‌های انتظاری:

### در `rubika-bot.service`:
```
🚀 Starting Rubika Bot...
🔄 Initializing bot client...
[INFO] No proxy configured  (یا proxy details)
[INFO] RubPy client initialized successfully
✅ Bot client initialized successfully
✅ Rubika Bot is running in webhook mode!
   Waiting for webhook requests...
```

### در `celery-worker.service`:
```
[INFO] Task rubika_bot.tasks.process_webhook_task started
[CELERY] process_webhook_task: update_type=Text
[RUBIKA_BOT] handle_update: chat_id=u123456, has_button=False, has_text=True
[INFO] Task 'process_webhook_task' succeeded.
```

---

## 🌐 تست Webhook

### 1. بررسی اینکه Webhook ثبت شده:

از پنل ادمین Django یا API:
```
https://your-domain.com/rubika_bot/settings/
```

یا با `curl`:
```bash
curl -X GET https://your-domain.com/rubika_bot/settings/webhook-info/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

### 2. تست ارسال پیام:

1. پیام `/start` به ربات بفرست
2. بررسی لاگ Celery:
   ```bash
   sudo journalctl -u celery-worker.service -n 50
   ```
3. باید ببینی: `[CELERY] process_webhook_task: succeeded`

---

## ⚠️ مشکلات احتمالی و راه‌حل:

### 1. Proxy Authentication Error (407)

**مشکل:**
```
HTTP/1.1 407 Proxy Authentication Required
```

**راه‌حل 1:** اضافه کردن Username/Password
```python
from rubika_bot.models import RubikaBotSettings
s = RubikaBotSettings.objects.first()
s.proxy_username = "your_username"
s.proxy_password = "your_password"
s.save()
```

**راه‌حل 2:** خاموش کردن Proxy
```python
from rubika_bot.models import RubikaBotSettings
s = RubikaBotSettings.objects.first()
s.proxy_enabled = False
s.save()
```

### 2. Celery Worker در حال اجرا نیست

```bash
sudo systemctl start celery-worker.service
sudo systemctl status celery-worker.service
```

### 3. Webhook ثبت نشده

از پنل ادمین:
```
Settings → Register Webhook
```

یا با API:
```bash
curl -X POST https://your-domain.com/rubika_bot/settings/register-webhook/
```

### 4. پیام‌ها به Webhook نمی‌رسن

**بررسی IP Allow List:**

```python
# در rubika_bot/views.py خط 63
def is_ip_allowed(ip):
    # بررسی کن که IP روبیکا allow شده باشه
```

**بررسی لاگ Nginx/Apache:**
```bash
tail -f /var/log/nginx/access.log | grep webhook
```

---

## 📊 معماری کامل:

```
[کاربر روبیکا]
      ↓
[سرور روبیکا] → POST https://your-domain.com/rubika_bot/webhook/
      ↓
[Django View: webhook_receiver]
      ↓
[Celery Task: process_webhook_task.delay(payload)]
      ↓ (async)
[Celery Worker]
      ↓
[RubPyIntegrationService.handle_webhook_payload()]
      ↓
[RubikaBotEngine.handle_update()]
      ↓
[پردازش دستور و ارسال پاسخ]
```

---

## 🎯 چک‌لیست نهایی:

- [ ] فایل‌های تغییر یافته آپلود شدند
- [ ] `celery-worker.service` در حال اجراست
- [ ] `rubika-bot.service` restart شد
- [ ] Proxy settings بررسی شد (یا خاموش شد)
- [ ] لاگ rubika-bot موفق بود: `RubPy client initialized successfully`
- [ ] Webhook ثبت شده (از پنل ادمین)
- [ ] تست: پیام `/start` به ربات فرستاده شد
- [ ] لاگ Celery موفق بود: `process_webhook_task: succeeded`

---

## 🔧 دستورات کامل (کپی-پیست):

```bash
# 1. آپلود فایل‌ها (با git)
cd /home/miepcoj/web/miepcoj.ir/public_html/HSC
git pull

# 2. غیرفعال کردن Proxy (اختیاری)
source venv/bin/activate
python manage.py shell --settings=HSCprojects.settings.production << EOF
from rubika_bot.models import RubikaBotSettings
s = RubikaBotSettings.objects.first()
s.proxy_enabled = False
s.save()
print("✅ Proxy disabled")
EOF

# 3. Restart سرویس‌ها
sudo systemctl restart rubika-bot.service
sudo systemctl restart celery-worker.service

# 4. بررسی وضعیت
echo "=== Rubika Bot Status ==="
sudo systemctl status rubika-bot.service --no-pager -l | tail -20

echo ""
echo "=== Celery Worker Status ==="
sudo systemctl status celery-worker.service --no-pager -l | tail -20

# 5. لاگ realtime
echo ""
echo "=== Watching logs (Ctrl+C to stop) ==="
sudo journalctl -u rubika-bot.service -u celery-worker.service -f
```

---

## 📞 اگر هنوز کار نکرد:

خروجی این دستورات رو بفرست:

```bash
# 1. وضعیت سرویس‌ها
sudo systemctl status rubika-bot.service celery-worker.service --no-pager

# 2. لاگ‌های اخیر
sudo journalctl -u rubika-bot.service -n 100 --no-pager
sudo journalctl -u celery-worker.service -n 100 --no-pager

# 3. تنظیمات
python manage.py shell --settings=HSCprojects.settings.production << EOF
from rubika_bot.models import RubikaBotSettings
s = RubikaBotSettings.objects.first()
print(f"Token: {'✅' if s.token else '❌'}")
print(f"Bot: {s.bot_username}")
print(f"Proxy: {s.proxy_enabled}")
if s.proxy_enabled:
    print(f"  URL: {s.get_masked_proxy_url()}")
EOF

# 4. Webhook logs در دیتابیس
python manage.py shell --settings=HSCprojects.settings.production << EOF
from rubika_bot.models import WebhookLog
recent = WebhookLog.objects.all()[:10]
for log in recent:
    print(f"[{log.log_type}] {log.title}: {log.message}")
EOF
```

---

تفاوت با Polling Mode:
- ✅ **Webhook**: سریع‌تر، کم‌مصرف‌تر، نیاز به Celery داره
- ❌ **Polling**: کندتر، بدون Celery کار می‌کنه، ساده‌تر

شما Webhook استفاده می‌کنید که انتخاب درستی هست! 🚀

