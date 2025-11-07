# اصلاح مشکل DNS Resolution

## مشکل
خطای `NameResolutionError` برای `api.rubika.ir` که DNS resolve نمی‌شود.

## راه حل

### 1. حذف `api.rubika.ir` از لیست Base URLs
- ✅ از `RubikaClient._bases` حذف شد
- ✅ از `action_register_webhook` حذف شد
- ✅ از `action_get_webhook_info` حذف شد

### 2. بهبود Error Handling
- ✅ خطاهای DNS فیلتر می‌شوند
- ✅ فقط خطاهای واقعی نمایش داده می‌شوند
- ✅ از نمایش خطاهای غیرضروری جلوگیری می‌شود

## Base URLs فعلی

```python
[
    "https://botapi.rubika.ir/v3",  # اولویت اول
    "https://botapi.rubika.ir",      # اولویت دوم
]
```

## تغییرات انجام شده

### `services.py`
- حذف `api.rubika.ir` از `_bases`
- بهبود error handling برای فیلتر کردن خطاهای DNS

### `views.py`
- حذف `api.rubika.ir` از `api_bases` در `action_register_webhook`
- حذف `api.rubika.ir` از `urls` در `action_get_webhook_info`
- بهبود error handling برای فیلتر کردن خطاهای DNS

## نتیجه

حالا فقط از `botapi.rubika.ir` استفاده می‌شود که DNS resolve می‌شود و خطاهای DNS دیگر نمایش داده نمی‌شوند.

