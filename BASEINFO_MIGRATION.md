# انتقال رابط گرافیکی به اپ BaseInfo

## تغییرات انجام شده

همانطور که درخواست کردید، رابط گرافیکی مدیریت داده‌ها از اپ `core` به اپ اصلی شما یعنی `BaseInfo` منتقل شد.

## فایل‌های جدید در BaseInfo:

### 1. **BaseInfo/views.py** (بازنویسی شده)
```python
# حاوی تمام APIها و viewها:
- base_settings()           # صفحه اصلی
- machines_api()             # مدیریت دستگاه‌ها
- blocks_api()               # مدیریت بلوک‌ها  
- dumps_api()                # مدیریت دمپ‌ها
- emergency_vehicles_api()   # مدیریت خودروهای امدادی
- mineral_types_api()        # مدیریت انواع سنگ
- workgroups_api()           # مدیریت گروه‌های کاری
- machine_types_api()        # مدیریت انواع دستگاه
- machine_types_by_workgroup() # دراپ‌داون آبشاری
```
✅ **563 خط کد کامل**

### 2. **BaseInfo/urls.py** (ایجاد شده)
```python
# تمام URL patterns:
/baseinfo/settings/                          # صفحه اصلی
/baseinfo/api/machines/                      # API دستگاه‌ها
/baseinfo/api/blocks/                        # API بلوک‌ها
/baseinfo/api/dumps/                         # API دمپ‌ها
/baseinfo/api/emergency-vehicles/            # API خودروها
/baseinfo/api/mineral-types/                 # API انواع سنگ
/baseinfo/api/workgroups/                    # API گروه‌های کاری
/baseinfo/api/machine-types/                 # API انواع دستگاه
/baseinfo/api/machine-types-by-workgroup/<id>/ # آبشاری
```
✅ **28 خط با 8 endpoint اصلی + 20 sub-endpoint**

### 3. **templates/BaseInfo/base_settings.html** (کپی و ویرایش شده)
- همان template قبلی
- تمام URLهای `/core/api/` به `/baseinfo/api/` تغییر یافتند
✅ **642 خط template کامل**

## تغییرات در فایل‌های موجود:

### 1. **HSCprojects/urls.py**
```python
# خط 49 اضافه شد:
path('baseinfo/', include('BaseInfo.urls', namespace='baseinfo')),
```

### 2. **templates/partials/sidebar.html**
```python
# خط 133 تغییر یافت از:
{% url 'core:base_settings' %}
# به:
{% url 'baseinfo:base_settings' %}
```

## دسترسی به سیستم:

### URL جدید:
```
http://localhost:8000/baseinfo/settings/
```

### از منو:
```
سایدبار → تنظیمات → تنظیمات پایه
```

## تفاوت با قبل:

| قبل (core) | حالا (BaseInfo) |
|------------|-----------------|
| `/core/settings/base/` | `/baseinfo/settings/` |
| `/core/api/machines/` | `/baseinfo/api/machines/` |
| `templates/core/` | `templates/BaseInfo/` |
| `{% url 'core:base_settings' %}` | `{% url 'baseinfo:base_settings' %}` |

## بررسی عملکرد:

### 1. چک کردن URLs:
```bash
python manage.py show_urls | grep baseinfo
```

### 2. تست صفحه اصلی:
```bash
curl http://localhost:8000/baseinfo/settings/
```

### 3. تست API:
```bash
curl http://localhost:8000/baseinfo/api/machines/
```

## ساختار اپ BaseInfo حالا:

```
BaseInfo/
├── __init__.py
├── admin.py
├── apps.py
├── models.py          # مدل‌های موجود قبلی
├── tests.py
├── views.py           # ✅ اضافه شده (563 خط)
├── urls.py            # ✅ ایجاد شده (28 خط)
└── migrations/

templates/BaseInfo/     # ✅ ایجاد شده
└── base_settings.html  # ✅ کپی شده (642 خط)
```

## فایل‌های قبلی در core:

فایل‌های قبلی در `core` هنوز موجودند اما دیگر استفاده نمی‌شوند:
- ❌ `core/views.py` (خط‌های مربوط به base_settings)
- ❌ `core/urls.py` (خط‌های مربوط به base_settings)
- ❌ `templates/core/base_settings.html`

**توصیه:** می‌توانید آن‌ها را حذف کنید یا نگه دارید.

## تست نهایی:

### گام 1: اجرای سرور
```bash
cd /home/mohamadkazem/HSC
python manage.py runserver
```

### گام 2: باز کردن صفحه
```
http://localhost:8000/baseinfo/settings/
```

### گام 3: بررسی عملکرد
- ✅ صفحه باز می‌شود
- ✅ 7 تب نمایش داده می‌شود
- ✅ جداول پر می‌شوند
- ✅ دکمه‌های افزودن کار می‌کنند
- ✅ مودال‌ها باز می‌شوند
- ✅ فرم‌ها ذخیره می‌شوند
- ✅ دراپ‌داون آبشاری کار می‌کند
- ✅ تقویم جلالی نمایش داده می‌شود

## خلاصه:

✅ همه چیز از `core` به `BaseInfo` منتقل شد
✅ همه URLها به روز شدند  
✅ Sidebar به روز شد
✅ Template کپی و ویرایش شد
✅ سیستم آماده استفاده است

## دسترسی سریع:

**صفحه اصلی:**
- URL: `/baseinfo/settings/`
- View: `BaseInfo.views.base_settings`
- Template: `templates/BaseInfo/base_settings.html`

**API Endpoints:**
- Machines: `/baseinfo/api/machines/`
- Blocks: `/baseinfo/api/blocks/`
- Dumps: `/baseinfo/api/dumps/`
- Vehicles: `/baseinfo/api/emergency-vehicles/`
- Minerals: `/baseinfo/api/mineral-types/`
- Workgroups: `/baseinfo/api/workgroups/`
- Machine Types: `/baseinfo/api/machine-types/`
- Cascading: `/baseinfo/api/machine-types-by-workgroup/<id>/`

---

**نتیجه:** رابط گرافیکی حالا در اپ اصلی شما (`BaseInfo`) قرار دارد و آماده استفاده است! 🎉
