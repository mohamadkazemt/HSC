# 🔧 راهنمای رفع مشکل ربات روبیکا

## 🎯 مشکلات شناسایی شده:

### 1. ربات در حالت Webhook بود (باید Polling باشه)
- ✅ تغییر `use_webhook=True` به `use_webhook=False`

### 2. Client هیچوقت Initialize نمی‌شد
- ✅ اضافه کردن `_ensure_client_initialized()` در `run_rubika_bot.py`

### 3. Proxy نیاز به Authentication داشت
- ✅ لاگ‌های بهتر برای debugging

### 4. پکیج rubika اشتباه بود (باید rubpy باشه)
- ✅ در سرور قبلاً نصب شد

---

## 📋 دستورات اجرا در سرور:

### مرحله 1: آپلود فایل‌های تغییر یافته

فایل‌های زیر تغییر کردند و باید به سرور آپلود شوند:
- `rubika_bot/services.py`
- `rubika_bot/management/commands/run_rubika_bot.py`

با `git pull` یا `scp` فایل‌ها رو به سرور منتقل کنید:

```bash
# در سرور:
cd /home/miepcoj/web/miepcoj.ir/public_html/HSC

# اگر از git استفاده می‌کنید:
git pull origin main

# یا فایل‌ها رو دستی آپلود کنید
```

### مرحله 2: نصب پکیج‌های مورد نیاز

```bash
cd /home/miepcoj/web/miepcoj.ir/public_html/HSC
source venv/bin/activate

# نصب aiohttp-socks برای proxy support
pip install aiohttp-socks==0.9.1

# اطمینان از نصب rubpy
pip list | grep rubpy
```

### مرحله 3: بررسی و تنظیم Proxy (اگر لازم باشه)

```bash
python manage.py shell --settings=HSCprojects.settings.production
```

در shell:

```python
from rubika_bot.models import RubikaBotSettings

settings = RubikaBotSettings.objects.first()

# بررسی تنظیمات فعلی
print(f"Proxy enabled: {settings.proxy_enabled}")
print(f"Proxy scheme: {settings.proxy_scheme}")
print(f"Proxy host: {settings.proxy_host}")
print(f"Proxy port: {settings.proxy_port}")
print(f"Proxy username: {settings.proxy_username}")
print(f"Has password: {bool(settings.proxy_password)}")

# اگر proxy username/password نیاز داره، اینجا ستش کن:
# settings.proxy_username = "your_username"
# settings.proxy_password = "your_password"
# settings.save()

# یا اگر proxy کار نمی‌کنه، خاموشش کن:
# settings.proxy_enabled = False
# settings.save()

# بررسی نهایی proxy URL
print(f"\nProxy URL: {settings.build_proxy_url()}")
print(f"Masked: {settings.get_masked_proxy_url()}")

exit()
```

### مرحله 4: Restart سرویس ربات

```bash
sudo systemctl restart rubika-bot.service
```

### مرحله 5: بررسی لاگ‌ها

```bash
# لاگ‌های realtime
sudo journalctl -u rubika-bot.service -f

# یا آخرین 50 خط
sudo journalctl -u rubika-bot.service -n 50 --no-pager
```

**چیزهایی که باید در لاگ ببینید:**
```
🚀 Starting Rubika Bot...
🔄 Initializing bot client...
[INFO] Proxy enabled: http://username@srv2.mkt0900.ir:21058
[INFO] Proxy connector created successfully: ...
[INFO] RubPy client initialized successfully
✅ Bot client initialized successfully
✅ Rubika Bot is running in polling mode!
```

---

## 🔍 عیب‌یابی (Troubleshooting)

### اگر خطای Proxy Authentication می‌گیرید:

**گزینه 1: اضافه کردن Username/Password**

```python
# در Django shell
from rubika_bot.models import RubikaBotSettings
settings = RubikaBotSettings.objects.first()
settings.proxy_username = "your_username_here"
settings.proxy_password = "your_password_here"
settings.save()
```

**گزینه 2: غیرفعال کردن Proxy**

```python
# در Django shell
from rubika_bot.models import RubikaBotSettings
settings = RubikaBotSettings.objects.first()
settings.proxy_enabled = False
settings.save()
```

بعد restart کنید:
```bash
sudo systemctl restart rubika-bot.service
```

### اگر ربات هنوز پیام‌ها رو دریافت نمی‌کنه:

1. **تست اتصال به روبیکا:**

```bash
cd /home/miepcoj/web/miepcoj.ir/public_html/HSC
source venv/bin/activate
python manage.py shell --settings=HSCprojects.settings.production
```

```python
from rubika_bot.services import RubPyIntegrationService
import time

print('Creating service instance...')
service = RubPyIntegrationService.get_instance()

print('Initializing client...')
service._ensure_client_initialized()

print('Client initialized! Waiting for messages...')
print('Send a test message to the bot now!')
time.sleep(60)  # Wait 60 seconds
print('Done.')
```

2. **بررسی توکن ربات:**

```python
from rubika_bot.models import RubikaBotSettings
settings = RubikaBotSettings.objects.first()
token = settings.get_token_safe()
print(f"Token exists: {bool(token)}")
print(f"Token length: {len(token) if token else 0}")
print(f"Bot username: {settings.bot_username}")
```

3. **تست دستی ربات:**

```bash
# توقف سرویس
sudo systemctl stop rubika-bot.service

# اجرای دستی
cd /home/miepcoj/web/miepcoj.ir/public_html/HSC
source venv/bin/activate
python manage.py run_rubika_bot

# حالا پیامی به ربات بفرستید و لاگ‌ها رو ببینید
# با Ctrl+C خارج بشید

# راه‌اندازی دوباره سرویس
sudo systemctl start rubika-bot.service
```

---

## 📊 بررسی نهایی

بعد از انجام تمام مراحل، این دستورات رو اجرا کنید:

```bash
# وضعیت سرویس
sudo systemctl status rubika-bot.service

# لاگ‌های اخیر
sudo journalctl -u rubika-bot.service -n 100 --no-pager

# بررسی پکیج‌ها
source venv/bin/activate
pip list | grep -E "(rubpy|aiohttp-socks)"
```

**انتظار داریم ببینیم:**
- ✅ Service: `active (running)`
- ✅ Logs: `RubPy client initialized successfully`
- ✅ Logs: `Rubika Bot is running in polling mode!`
- ✅ Packages: `rubpy==7.1.32` و `aiohttp-socks==0.9.1`

---

## 🎉 تست نهایی

1. پیام `/start` به ربات بفرستید
2. بررسی کنید که ربات جواب می‌ده
3. لاگ‌ها رو بررسی کنید:
   ```bash
   sudo journalctl -u rubika-bot.service -f
   ```
4. باید ببینید: `[RUBIKA_BOT] handle_update: chat_id=...`

---

## 📞 اگر هنوز مشکل دارید

اطلاعات زیر رو جمع‌آوری و ارسال کنید:

```bash
# 1. وضعیت سرویس
sudo systemctl status rubika-bot.service

# 2. لاگ‌های کامل
sudo journalctl -u rubika-bot.service -n 200 --no-pager

# 3. تنظیمات ربات
python manage.py shell --settings=HSCprojects.settings.production << EOF
from rubika_bot.models import RubikaBotSettings
s = RubikaBotSettings.objects.first()
print(f"Token exists: {bool(s.token)}")
print(f"Proxy: {s.proxy_enabled}")
print(f"Proxy URL: {s.get_masked_proxy_url()}")
EOF

# 4. پکیج‌ها
pip list | grep -E "(rubpy|rubika|aiohttp)"
```

