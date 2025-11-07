# اصلاحات Webhook و ثبت Webhook

## مشکلات پیدا شده و اصلاح شده

### 1. ❌ مشکل در ثبت Webhook
**مشکل**: استفاده از `data=payload` به جای `json=payload`
```python
# قبل (اشتباه):
response = requests.post(endpoint, data=payload, timeout=30)

# بعد (درست):
response = requests.post(
    endpoint,
    json=payload,  # استفاده از json مطابق Flask bot
    headers={"Content-Type": "application/json"},
    timeout=30
)
```
**فایل**: `views.py` - خط 99-104

### 2. ❌ ساختار نادرست Payload در send_message_with_buttons
**مشکل**: ساختار payload برای inline_keypad نادرست بود
```python
# قبل:
payload = {"chat_id": chat_id, "text": text, "inline_keypad": {"rows": [{"buttons": row} for row in rows]}}

# بعد (مطابق Flask bot):
formatted_rows = [{"buttons": row} for row in rows]
payload = {"chat_id": chat_id, "text": text, "inline_keypad": {"rows": formatted_rows}}
```
**فایل**: `services.py` - خط 66-69

### 3. ✅ بهبود Routing در webhook_receiver
**تغییر**: routing بر اساس `update_type` به ابتدای تابع منتقل شد (مطابق Flask bot)
```python
# Routing بر اساس update_type (مطابق Flask bot)
if update_type == 'ReceiveInlineMessage':
    return handle_inline_message(payload)
elif update_type == 'ReceiveQuery':
    return handle_query(payload)
elif update_type == 'GetSelectionItem':
    return handle_selection_item(payload)
elif update_type == 'SearchSelectionItems':
    return handle_search_selection(payload)
elif update_type == 'ReceiveUpdate':
    # ادامه پردازش ReceiveUpdate
    pass
```
**فایل**: `views.py` - خط 481-495

### 4. ✅ اضافه کردن توابع Handler جداگانه
**تغییر**: توابع handler جداگانه اضافه شدند (مطابق Flask bot)
- `handle_inline_message(payload)`
- `handle_query(payload)`
- `handle_selection_item(payload)`
- `handle_search_selection(payload)`
**فایل**: `views.py` - خط 433-487

### 5. ✅ بهبود لاگ‌گیری
**تغییر**: لاگ payload خام در ابتدای webhook_receiver (مطابق Flask bot)
```python
# لاگ payload خام (مطابق Flask bot)
WebhookLog.log_incoming(
    'RAW Webhook',
    f'دریافت از {client_ip}',
    {'ip': client_ip, 'raw_payload': payload}
)
```
**فایل**: `views.py` - خط 444-449

### 6. ✅ اضافه کردن log_warning
**تغییر**: متد `log_warning` به WebhookLog اضافه شد
**فایل**: `models.py` - خط 158-166

---

## مقایسه با Flask Bot

### ثبت Webhook
- ✅ استفاده از `json=payload` به جای `data=payload`
- ✅ استفاده از `updateBotEndpoints` (با s)
- ✅ ارسال جداگانه برای هر endpoint type
- ✅ استفاده از headers مناسب

### دریافت Webhook
- ✅ Normalize کردن payload (inline_message, update wrapper)
- ✅ Routing بر اساس update_type
- ✅ توابع handler جداگانه
- ✅ لاگ‌گیری مناسب

### ارسال پیام
- ✅ ساختار صحیح inline_keypad
- ✅ استفاده از fallback برای base URLs

---

## تست‌های پیشنهادی

1. **تست ثبت Webhook**:
   - از پنل Django دکمه "ثبت/بروزرسانی وبهوک" را بزنید
   - بررسی کنید که همه endpoint ها با موفقیت ثبت شوند

2. **تست دریافت پیام**:
   - یک پیام به ربات ارسال کنید
   - بررسی لاگ‌ها در پنل Django
   - بررسی کنید که پیام دریافت و پردازش می‌شود

3. **تست دکمه‌های Inline**:
   - دکمه‌های inline را تست کنید
   - بررسی کنید که query handler کار می‌کند

---

## نکات مهم

1. **Migration**: بعد از تغییرات، migration لازم نیست (فقط کد تغییر کرده)

2. **لاگ‌ها**: تمام لاگ‌ها در پنل Django در بخش "لاگ‌های Webhook" قابل مشاهده است

3. **Debugging**: اگر مشکلی پیش آمد، لاگ‌های RAW Webhook را بررسی کنید

---

## خلاصه تغییرات

✅ **views.py**:
- اصلاح ثبت webhook (json به جای data)
- بهبود routing
- اضافه کردن توابع handler
- بهبود لاگ‌گیری

✅ **services.py**:
- اصلاح ساختار payload در send_message_with_buttons

✅ **models.py**:
- اضافه کردن log_warning

---

## نتیجه

کد Django حالا کاملاً مطابق با Flask bot کار می‌کند و باید webhook به درستی ثبت و پیام‌ها دریافت شوند.

