# اصلاح مشکل دریافت اطلاعات Webhook

## مشکل
هنگام تست webhook، خطای "نتوانست اطلاعات را دریافت کند" رخ می‌دهد.

## تغییرات انجام شده

### 1. بهبود `get_bot_endpoint` در `RubikaClient`
- ✅ Error handling بهتر
- ✅ لاگ کردن خطاهای دقیق
- ✅ بررسی status code و response format
- ✅ مدیریت timeout و connection errors

### 2. بهبود `action_get_webhook_info` در `views.py`
- ✅ استفاده از `RubikaClient.get_bot_endpoint()`
- ✅ Fallback به روش مستقیم در صورت نیاز
- ✅ Error handling بهتر با جزئیات بیشتر
- ✅ لاگ کردن خطاها برای debugging

## نکات مهم

### ممکن است API روبیکا endpoint `getBotEndpoint` نداشته باشد
اگر هنوز خطا می‌دهد، ممکن است:
1. API روبیکا این endpoint را پشتیبانی نکند
2. نیاز به authentication خاصی باشد
3. نام endpoint متفاوت باشد

### راه حل جایگزین
اگر `getBotEndpoint` کار نمی‌کند، می‌توانید:
1. از لاگ‌های webhook استفاده کنید
2. مستقیماً از پنل روبیکا بررسی کنید
3. با ثبت مجدد webhook، وضعیت را بررسی کنید

## تست
حالا باید خطاهای دقیق‌تری در response دریافت کنید که به debugging کمک می‌کند.

