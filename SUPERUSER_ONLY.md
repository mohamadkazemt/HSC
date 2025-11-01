# محدودسازی دسترسی تنظیمات پایه به Superuser

## تغییرات امنیتی انجام شده

دسترسی به **تنظیمات پایه** (Base Settings) حالا فقط برای **ادمین اصلی Django (Superuser)** محدود شده است.

## تغییرات:

### 1. **BaseInfo/views.py**

#### قبل:
```python
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required  # هر staff می‌تونست دسترسی داشته باشه
def base_settings(request):
    ...
```

#### بعد:
```python
from django.contrib.admin.views.decorators import user_passes_test

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)  # فقط superuser
def base_settings(request):
    ...
```

✅ **همه viewها و APIها** حالا با `@user_passes_test(is_superuser)` محافظت می‌شوند.

### 2. **templates/partials/sidebar.html**

#### قبل:
```django
<li>
  <a href="{% url 'baseinfo:base_settings' %}">
    تنظیمات پایه
  </a>
</li>
```

#### بعد:
```django
{% if user.is_superuser %}
<li>
  <a href="{% url 'baseinfo:base_settings' %}">
    تنظیمات پایه
  </a>
</li>
{% endif %}
```

✅ منوی "تنظیمات پایه" فقط برای superuser نمایش داده می‌شود.

## چک کردن Superuser:

### در Django Shell:
```python
python manage.py shell

>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='your_username')
>>> print(user.is_superuser)
True  # اگر superuser باشد
False # اگر staff عادی باشد
```

### ایجاد Superuser جدید:
```bash
python manage.py createsuperuser
```

## تفاوت Staff و Superuser:

| ویژگی | Staff (`is_staff=True`) | Superuser (`is_superuser=True`) |
|-------|------------------------|----------------------------------|
| دسترسی به Admin Panel | ✅ | ✅ |
| ویرایش محتوا | ✅ (با permission) | ✅ (همه چیز) |
| دسترسی به تنظیمات پایه | ❌ | ✅ |
| حذف کاربران | ❌ | ✅ |
| تغییر permissions | ❌ | ✅ |

## سطوح دسترسی در سیستم:

### 1. کاربر عادی:
```python
is_staff = False
is_superuser = False
```
- ❌ دسترسی به Admin Panel
- ❌ دسترسی به تنظیمات پایه

### 2. Staff:
```python
is_staff = True
is_superuser = False
```
- ✅ دسترسی به Admin Panel (با permission)
- ❌ دسترسی به تنظیمات پایه

### 3. Superuser (ادمین اصلی):
```python
is_staff = True
is_superuser = True
```
- ✅ دسترسی کامل به Admin Panel
- ✅ دسترسی به تنظیمات پایه

## تست دسترسی:

### تست 1: با حساب Superuser
```bash
# لاگین با superuser
# منوی "تنظیمات پایه" باید نمایش داده شود
# صفحه باید باز شود
```
✅ **باید کار کند**

### تست 2: با حساب Staff عادی
```bash
# لاگین با staff (is_staff=True, is_superuser=False)
# منوی "تنظیمات پایه" نباید نمایش داده شود
# اگر URL را مستقیم باز کنید، خطای 403 یا redirect می‌دهد
```
❌ **دسترسی نداره**

### تست 3: دسترسی مستقیم به URL
```bash
# با حساب staff به این URL بروید:
http://localhost:8000/baseinfo/settings/
```

**نتیجه:**
- اگر **superuser** باشید: صفحه باز می‌شود ✅
- اگر **staff** باشید: به صفحه لاگین redirect می‌شوید یا خطای 403 ❌
- اگر **کاربر عادی** باشید: به صفحه لاگین redirect می‌شوید ❌

## پیام‌های خطا:

### اگر staff (نه superuser) بخواهد وارد شود:
```
Permission Denied (403)
You don't have permission to access this page.
```

### اگر کاربر لاگین نکرده باشد:
```
Redirect به: /accounts/login/?next=/baseinfo/settings/
```

## چرا این تغییر مهم است؟

### ✅ امنیت بیشتر:
- تنظیمات پایه حساس هستند (دستگاه‌ها، بلوک‌ها، خودروها)
- فقط ادمین اصلی باید بتواند این داده‌ها را تغییر دهد

### ✅ جلوگیری از اشتباه:
- staff‌های عادی نمی‌توانند به اشتباه داده‌های مهم را حذف کنند

### ✅ کنترل دسترسی:
- تفکیک واضح بین staff و superuser

## اگر می‌خواهید یک staff خاص دسترسی داشته باشد:

### گزینه 1: تبدیل به Superuser (توصیه نمی‌شود)
```python
from django.contrib.auth.models import User
user = User.objects.get(username='username')
user.is_superuser = True
user.save()
```

### گزینه 2: ایجاد Permission سفارشی (پیشرفته)
در `BaseInfo/models.py` یک Meta class اضافه کنید:
```python
class Meta:
    permissions = [
        ("can_manage_base_settings", "Can manage base settings"),
    ]
```

سپس در `views.py`:
```python
from django.contrib.auth.decorators import permission_required

@permission_required('BaseInfo.can_manage_base_settings')
def base_settings(request):
    ...
```

## خلاصه:

✅ همه viewها محافظت شدند با `@user_passes_test(is_superuser)`
✅ منوی سایدبار فقط برای superuser نمایش داده می‌شود
✅ دسترسی مستقیم به URL هم محافظت شده
✅ امنیت سیستم افزایش یافت

---

**نتیجه:** حالا فقط **ادمین اصلی (Superuser)** می‌تواند به تنظیمات پایه دسترسی داشته باشد! 🔒
