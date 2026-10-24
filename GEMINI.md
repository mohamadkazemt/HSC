# GEMINI.md — راهنمای ایجنت پروژه HSC

مرجع جامع و به‌روز قوانین و ساختار پروژه در فایل [AGENTS.md](file:///d:/MYPJ/HSC/AGENTS.md) قرار دارد.

## نکات کلیدی جهت صرفه‌جویی در مصرف توکن:
1. **شاخه اصلی:** `mkt` (همیشه `git push origin mkt` و `git push origin mkt:master`).
2. **سرور پروداکشن:** `45.82.136.228` (استقرار خودکار با اسکریپت `/usr/local/bin/hsc-deploy.sh`).
3. **تنظیمات پروژه:**
   - پروداکشن: `HSCprojects.settings.production`
   - تست‌ها: `HSCprojects.settings.testing`
   - محلی: `HSCprojects.settings.development`
4. **دستور اجرای تست‌ها:**
   `.\.venv\Scripts\python.exe manage.py test accounts.test_dependents rubika_bot.test_dependents_bot --settings=HSCprojects.settings.testing`
5. **قانون امنیتی قالب‌های جنگو:** هرگز از متغیرهای با پیشوند آندرلاین مانند `errors.__all__` در قالب استفاده نکنید.
6. **فایل‌های سنگین:** فایل‌های سشن گذشته (`new-session*.json`) را اسکن نکنید.

برای جزییات کامل ساختار تمام اپلیکیشن‌ها و دستورات سرور، مستقیماً به [AGENTS.md](file:///d:/MYPJ/HSC/AGENTS.md) مراجعه فرمایید.
