# راه حل مشکل Migration

## مشکل
جدول `rubika_bot_webhooklog` از قبل در دیتابیس وجود دارد، اما migration 0003 می‌خواهد دوباره آن را ایجاد کند که باعث خطا می‌شود.

## راه حل
Migration 0003 اصلاح شد تا فقط indexes را اضافه کند، نه جدول را.

## دستورات اجرا

### گزینه 1: Fake کردن migration (اگر جدول از قبل وجود دارد)
```bash
DJANGO_SETTINGS_MODULE='HSCprojects.settings.production' python manage.py migrate rubika_bot 0003 --fake
```

### گزینه 2: اجرای migration اصلاح شده
```bash
DJANGO_SETTINGS_MODULE='HSCprojects.settings.production' python manage.py migrate rubika_bot
```

## توضیحات
- Migration 0003 حالا فقط indexes را اضافه می‌کند
- از `IF NOT EXISTS` استفاده می‌کند تا اگر index از قبل وجود دارد، خطا ندهد
- جدول را ایجاد نمی‌کند چون از قبل وجود دارد

## اگر هنوز مشکل دارید
اگر migration هنوز خطا می‌دهد، می‌توانید migration را fake کنید:

```bash
DJANGO_SETTINGS_MODULE='HSCprojects.settings.production' python manage.py migrate rubika_bot 0003 --fake
```

این دستور به Django می‌گوید که migration را اجرا شده در نظر بگیرد بدون اینکه واقعاً اجرا کند.

