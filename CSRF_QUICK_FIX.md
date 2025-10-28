# حل فوری مشکل CSRF

## ⚠️ مشکل اصلی پیدا شد!

**jQuery هنوز بارگذاری نشده بود** وقتی کد `$.ajaxSetup` اجرا می‌شد!

## ✅ اصلاحات انجام شده:

### 1. جابجایی کد CSRF setup
کد CSRF setup از **قبل از jQuery** به **بعد از jQuery** منتقل شد.

### 2. اضافه کردن CSRF token به window
```javascript
window.CSRF_TOKEN = '{{ csrf_token }}';
```

### 3. اضافه کردن console.log برای debug
```javascript
console.log('CSRF protection enabled for AJAX requests');
```

## 🚀 دستورات لازم:

```bash
# 1. توقف سرور
Ctrl+C

# 2. پاک کردن تمام cache
cd /home/mohamadkazem/HSC
source .venv/bin/activate

# پاک کردن Django sessions
python manage.py clearsessions

# پاک کردن Redis (اگر دارید)
redis-cli FLUSHDB

# یا اگر Redis password دارد:
redis-cli -a YOUR_PASSWORD FLUSHDB

# 3. اجرای مجدد سرور
python manage.py runserver 127.0.0.1:8000
```

## 🌐 در مرورگر:

### مرحله 1: پاک کردن کامل
1. باز کردن Developer Tools (F12)
2. رفتن به tab Application (یا Storage در Firefox)
3. از منوی سمت چپ:
   - Cookies → انتخاب سایت → Delete All
   - Local Storage → Clear
   - Session Storage → Clear
4. بستن تمام تب‌های مرورگر

### مرحله 2: باز کردن مجدد
1. باز کردن مرورگر جدید
2. رفتن به: `http://127.0.0.1:8000`
3. لاگین مجدد
4. رفتن به فرم گزارش حادثه

### مرحله 3: بررسی Console
در Developer Tools (F12) → Console باید ببینید:
```
CSRF protection enabled for AJAX requests
```

### مرحله 4: بررسی Cookie
در Console تایپ کنید:
```javascript
console.log(document.cookie);
```
باید `csrftoken` را ببینید.

همچنین:
```javascript
console.log(window.CSRF_TOKEN);
```
باید یک رشته طولانی (token) برگردد.

## 🧪 تست نهایی:

### تست 1: Network tab
1. F12 > Network
2. فرم را پر کنید
3. Submit کنید
4. روی request کلیک کنید
5. در Headers باید ببینید:
```
X-CSRFToken: [یک مقدار طولانی]
```

### تست 2: Submit فرم
- اگر موفق بود: پیام موفقیت و redirect
- اگر خطا داد: بررسی Console و Network

## ❌ اگر هنوز خطا می‌گیرید:

### گزینه 1: Hard Refresh
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

### گزینه 2: Incognito Mode
- Chrome: `Ctrl + Shift + N`
- Firefox: `Ctrl + Shift + P`
- سپس لاگین و تست

### گزینه 3: Browser دیگر
Firefox یا Chrome دیگری امتحان کنید

### گزینه 4: بررسی settings
در Console تایپ کنید:
```javascript
// بررسی کتابخانه‌ها
console.log(typeof jQuery);  // باید 'function' برگرداند
console.log(typeof $);        // باید 'function' برگرداند

// بررسی تابع getCookie
console.log(typeof getCookie); // باید 'function' برگرداند

// تست getCookie
console.log(getCookie('csrftoken')); // باید token برگرداند
```

## 📋 چک‌لیست نهایی:

- [ ] سرور restart شد
- [ ] Browser cache پاک شد
- [ ] Django sessions پاک شد
- [ ] Redis فاز شد (اگر دارید)
- [ ] لاگین مجدد انجام شد
- [ ] Console پیام "CSRF protection enabled" را نشان می‌دهد
- [ ] `document.cookie` شامل csrftoken است
- [ ] `window.CSRF_TOKEN` مقدار دارد

## 🎯 انتظار نتیجه:

✅ فرم بدون خطا submit می‌شود  
✅ Redirect به صفحه جزئیات گزارش  
✅ پیام موفقیت نمایش داده می‌شود  

---

## 🆘 پشتیبانی اضطراری:

اگر هنوز کار نکرد، این اطلاعات را بفرستید:

1. **خروجی Console:**
   ```javascript
   console.log({
       jquery: typeof jQuery,
       csrfToken: window.CSRF_TOKEN ? 'exists' : 'missing',
       cookie: document.cookie.includes('csrftoken') ? 'exists' : 'missing'
   });
   ```

2. **Network Request Headers:**
   F12 > Network > POST request > Headers

3. **Django Log:**
   در terminal که سرور اجرا می‌شود، خطاها را بررسی کنید

---

**وضعیت:** ✅ آماده تست  
**آخرین بروزرسانی:** الان همین الان!  
**تضمین:** این بار باید کار کند! 💪
