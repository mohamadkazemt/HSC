# AGENTS.md — راهنمای جامع ایجنت‌های هوش مصنوعی برای پروژه HSC

این سند مرجع اصلی و فشرده برای هر ایجنت (Agent) هوش مصنوعی است تا بدون نیاز به پیمایش کل پروژه یا جستجو در فایل‌های حجیم، مستقیماً ساختار، دستورات، سرور، و الزامات پروژه را بشناسد و در مصرف توکن صرفه‌جویی شود.

---

## ۱. هویت و معماری کلی پروژه
- **نام پروژه:** سامانه جامع HSE و منابع انسانی (HSC)
- **فریم‌ورک:** Django 5.1 (پایتون) + Celery + Redis + PostgreSQL (پروداکشن) / SQLite (تست)
- **دامنه عمومی:** `miepcoj.ir`
- **شاخه اصلی فعال گیت:** `mkt` (کدها روی `origin/mkt` و همگام با `origin/master` نگه داشته می‌شوند)

### نقشه ماژول‌ها و اپلیکیشن‌های کلیدی
| ماژول / مسیر | توضیحات و وظایف | مسیرهای مهم |
|---|---|---|
| `accounts/` | مدیریت پرسنل، پرتال تحت تکفل (`/d/`)، اعتبارسنجی پیامکی (OTP)، درخواست‌های تغییر اطلاعات تکفل، پنل بازبینی منابع انسانی | `accounts/dependent_views.py`<br>`accounts/dependent_service.py`<br>`accounts/portal_urls.py`<br>`accounts/models.py` |
| `rubika_bot/` | ربات روبیکا (وبهوک `/rubika/webhook/` و پولینگ)، منوی تحت تکفل، ثبت گزارشات و مرخصی از روبیکا | `rubika_bot/services.py`<br>`rubika_bot/views.py`<br>`rubika_bot/urls.py` |
| `dashboard/` | داشبورد اصلی، اعلان‌ها، سیستم ارسال پیامک (`sms_utils.py`)، لاگ فعالیت کاربران | `dashboard/views.py`<br>`dashboard/sms_utils.py` |
| `message_center/` | مرکز پیام، اعلان‌های سراسری و لاگ پیام‌های سیستمی | `message_center/` |
| `checklist_app/` | چک‌لیست‌های دوره‌ای، ماشین‌آلات و پیمانکاران | `checklist_app/` |
| `machine_checklist/` | چک‌لیست‌های اختصاصی ماشین‌آلات معدنی | `machine_checklist/` |
| `anomalis/` | ثبت آنومالی‌ها، اقدامات اصلاحی و گزارش‌های ایمنی | `anomalis/` |
| `fire_reports/` | گزارش‌های آتش‌نشانی و تجهیزات اطفاء حریق | `fire_reports/` |
| `leave_reports/` | گردش کار تایید مرخصی‌ها و سلسله‌مراتب تایید | `leave_reports/` |
| `permissions/` | کنترل دسترسی‌های دانه‌ای (Granular Permissions) | `permissions/` |
| `HSCprojects/` | تنظیمات اصلی پروژه و مسیریابی ریشه | `HSCprojects/urls.py`<br>`HSCprojects/settings/` |

---

## ۲. تنظیمات محیطی (Settings)
پروژه از ساختار چند فایلی در `HSCprojects/settings/` استفاده می‌کند:
- **توسعه محلی:** `HSCprojects.settings.development` (پایگاه داده SQLite محلی)
- **تست‌ها:** `HSCprojects.settings.testing` (اجرای سریع یونیت‌تست‌ها با کش مجزا)
- **پروداکشن:** `HSCprojects.settings.production` (پایگاه داده PostgreSQL `hsc_production`، ردیس، کش، لاگینگ و غیره)

---

## ۳. سرور پروداکشن و دستورات اتصال
- **آی‌پی سرور:** `45.82.136.228`
- **کاربر:** `root` (و سرویس‌ها با `hsc_admin`)
- **کلید SSH محلی:** `C:\Users\mkt29\.ssh\id_ed25519`
- **دستور اتصال SSH:**
  ```powershell
  ssh -i "C:\Users\mkt29\.ssh\id_ed25519" -o IdentitiesOnly=yes root@45.82.136.228
  ```
- **مسیر پروژه روی سرور:** `/var/www/HSC`
- **محیط مجازی پایتون سرور:** `/var/www/HSC/venv/bin/python` (توجه: پایتون سرور نسخه 3.14 است)
- **لاگ‌های پروداکشن:** `/var/www/HSC/logs/production.log`
- **دستور مشاهده لاگ زنده:**
  ```powershell
  ssh -i "C:\Users\mkt29\.ssh\id_ed25519" -o IdentitiesOnly=yes root@45.82.136.228 "tail -n 50 /var/www/HSC/logs/production.log"
  ```

---

## ۴. چرخه استقرار (Deploy)
روی سرور یک اسکریپت خودکار استقرار در مسیر `/usr/local/bin/hsc-deploy.sh` قرار دارد.
این اسکریپت کارهای زیر را انجام می‌دهد:
1. `git fetch origin mkt` و `git reset --hard origin/mkt`
2. بررسی تغییرات `requirements.txt` و نصب در صورت نیاز
3. اجرای مایگریشن‌ها با `DJANGO_SETTINGS_MODULE=HSCprojects.settings.production`
4. اجرای `collectstatic`
5. اعمال پچ‌های سازگاری Python 3.14
6. راه‌اندازی مجدد `gunicorn` و `celery-worker`
7. اجرای Smoke Test با ارسال درخواست HTTP به `miepcoj.ir`

### نحوه دیپلوی پس از کامیت:
```powershell
# ۱. پوش تغییرات به گیت‌هاب (هم مکت و هم مستر)
git push origin mkt
git push origin mkt:master

# ۲. اجرای اسکریپت دیپلوی روی سرور
ssh -i "C:\Users\mkt29\.ssh\id_ed25519" -o IdentitiesOnly=yes root@45.82.136.228 "/usr/local/bin/hsc-deploy.sh"
```

> **نکته پروکسی گیت (Windows):** در صورتی که اتصال مستقیم به گیت‌هاب با خطای `curl 28 Failed to connect` مواجه شد، از پروکسی محلی سیستم استفاده کنید:
> ```powershell
> git -c http.proxy=http://127.0.0.1:10809 push origin mkt
> git -c http.proxy=http://127.0.0.1:10809 push origin mkt:master
> ```

---

## ۵. دستورات کاربردی و تست‌ها (Cheatsheet)

### اجرای تست‌های محلی
```powershell
.\.venv\Scripts\python.exe manage.py test accounts.test_dependents rubika_bot.test_dependents_bot --settings=HSCprojects.settings.testing
```

### اجرای شل جنگو در محیط پروداکشن
```powershell
ssh -i "C:\Users\mkt29\.ssh\id_ed25519" -o IdentitiesOnly=yes root@45.82.136.228 "/var/www/HSC/venv/bin/python /var/www/HSC/manage.py shell --settings=HSCprojects.settings.production"
```

### بررسی وضعیت سرویس‌ها روی سرور
```powershell
ssh -i "C:\Users\mkt29\.ssh\id_ed25519" -o IdentitiesOnly=yes root@45.82.136.228 "systemctl status gunicorn celery-worker nginx"
```

---

## ۶. دام‌های مهم و قوانین کدنویسی (Gotchas & Critical Rules)

1. **محدودیت نام متغیرها در قالب جنگو (Django Templates):**
   - به هیچ وجه در تگ‌های قالب جنگو (`{{ ... }}` یا `{% if ... %}`) نباید به ویژگی‌ها یا کلیدهایی که با آندرلاین (`_`) شروع می‌شوند دسترسی پیدا کرد (مانند `errors.__all__` یا `obj._state`). این کار بلافاصله `TemplateSyntaxError` با خطای ۵۰۰ تولید می‌کند.
   - راهکار: متغیرهای مورد نظر را در پایتون استخراج و با نام استاندارد (مثل `non_field_error`) به کانتکست پاس دهید.

2. **فرمان‌های پاورشل در ویندوز (PowerShell CLI):**
   - از نوشتن کاراکترهای فارسی چندخطی در دستورات مستقیم PowerShell با دابل کوتیشن خودداری کنید تا با خطای انکودینگ `charmap` متوقف نشود. اسکریپت‌ها را در فایل موقت ذخیره کرده یا از پایتون / پایپ ورودی (`@' ... '@ | ...`) استفاده کنید.
   - عملگر `&&` در برخی نسخه‌های PowerShell پشتیبانی نمی‌شود؛ از `;` به عنوان جداکننده دستورات استفاده کنید.

3. **پایتون ۳.۱۴ روی سرور پروداکشن:**
   - سرور پروداکشن از Python 3.14 استفاده می‌کند که برخی کتابخانه‌ها نیازمند پچ‌های سازگاری هستند. این پچ‌ها به طور خودکار توسط `hsc-deploy.sh` اعمال می‌شوند، ولی هنگام تغییر کدهای ناهمگام (asyncio / aiohttp) به سازگاری نسخه‌ای دقت فرمایید.

4. **فایل‌های سنگین و جلوگیری از سوختن توکن:**
   - فایل‌های لاگ، فایل‌های سنگین مانند `new-session*.json` (خروجی سشن‌های قبلی چت) و دیتابیس‌های تست نیازی به خواندن ندارند. برای جستجو همیشه از فیلترهای مناسب مانند `--include "*.py"` استفاده کنید.
   - قبل از انجام تحلیل یا کدنویسی مجدد، ساختارهای آماده در `accounts/dependent_service.py` و `rubika_bot/services.py` را مرور کنید و از دوباره‌کاری خودداری نمایید.
