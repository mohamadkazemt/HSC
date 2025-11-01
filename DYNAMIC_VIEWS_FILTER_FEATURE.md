# قابلیت فیلتر پویای صفحات موجود

## خلاصه
این قابلیت باعث می‌شود که هنگام انتخاب یک موجودیت (قسمت، بخش، گروه، سمت یا کاربر)، فقط صفحاتی که آن موجودیت هنوز به آن‌ها دسترسی ندارد در لیست انتخاب صفحات نمایش داده شود.

## مشکلی که حل می‌شود
قبل از این قابلیت:
- ✗ تمام صفحات برای همه موجودیت‌ها نمایش داده می‌شد
- ✗ امکان ایجاد دسترسی تکراری وجود داشت
- ✗ کاربر نمی‌دانست کدام صفحات قبلاً تعریف شده‌اند

بعد از این قابلیت:
- ✓ فقط صفحات بدون دسترسی نمایش داده می‌شوند
- ✓ از ایجاد دسترسی تکراری جلوگیری می‌شود
- ✓ اگر همه دسترسی‌ها تعریف شده باشند، پیغام هشدار نمایش داده می‌شود
- ✓ دکمه ذخیره غیرفعال می‌شود اگر صفحه‌ای موجود نباشد

---

## تغییرات انجام شده

### 1. Backend - ویوی AJAX جدید
**فایل:** `permissions/views.py`

```python
@user_passes_test(is_staff_user)
def get_available_views(request):
    """
    ویوی AJAX برای دریافت صفحاتی که موجودیت انتخاب شده هنوز به آن‌ها دسترسی ندارد.
    """
    entity_type = request.GET.get('entity_type')
    entity_id = request.GET.get('entity_id')
    
    # دریافت تمام ویوها
    all_views = get_all_views_with_labels()
    
    # دریافت ویوهایی که از قبل دسترسی دارند
    existing_view_names = set()
    
    if entity_type == 'part':
        existing_view_names = set(
            PartPermission.objects.filter(part_id=entity_id).values_list('view_name', flat=True)
        )
    # ... (برای سایر انواع)
    
    # فیلتر کردن - فقط آن‌هایی که دسترسی ندارند
    available_views = [
        view for view in all_views 
        if view['name'] not in existing_view_names
    ]
    
    return JsonResponse({'views': available_views}, safe=False)
```

**ویژگی‌ها:**
- دریافت نوع موجودیت و شناسه آن از پارامترهای GET
- استخراج لیست صفحاتی که قبلاً دسترسی دارند
- فیلتر کردن و بازگشت فقط صفحات موجود
- پشتیبانی از تمام انواع موجودیت (قسمت، بخش، گروه، سمت، کاربر)

---

### 2. URL Route جدید
**فایل:** `permissions/urls.py`

```python
path('available-views/', views.get_available_views, name='get_available_views'),
```

---

### 3. Frontend - تغییرات JavaScript
**فایل:** `templates/permissions/manage_access.html`

#### الف) متغیر جدید برای شمارش صفحات موجود
```javascript
availableViewsCount: 0,
```

#### ب) به‌روزرسانی لیست صفحات هنگام تغییر موجودیت
```javascript
.on('change', (e)=>{
  this.selectedEntityId = e.target.value;
  // به‌روزرسانی لیست صفحات
  if(this.selectedEntityId){
    this.updateAvailableViews();
  }
});
```

#### ج) تابع جدید برای دریافت و نمایش صفحات موجود
```javascript
async updateAvailableViews(){
  const el = this.$refs.viewsSelect;
  
  // فراخوانی AJAX
  const url = '{% url "permissions:get_available_views" %}?entity_type=' + 
               this.entityType + '&entity_id=' + this.selectedEntityId;
  const response = await fetch(url);
  const data = await response.json();
  
  // پاک کردن و به‌روزرسانی لیست
  $(el).empty();
  
  if(data.views && data.views.length > 0){
    this.availableViewsCount = data.views.length;
    data.views.forEach(view => {
      $(el).append(new Option(view.label, view.name, false, false));
    });
  } else {
    this.availableViewsCount = 0;
    $(el).append(new Option('همه دسترسی‌ها قبلاً تعریف شده‌اند', '', true, true));
  }
  
  // راه‌اندازی مجدد select2
  $(el).select2({ ... });
}
```

---

### 4. UI/UX بهبودها

#### الف) پیغام هشدار
اگر همه صفحات قبلاً تعریف شده باشند، یک پیغام هشدار زرد نمایش داده می‌شود:

```html
<div x-show="selectedEntityId && availableViewsCount === 0" class="...">
  ⚠️ تمام دسترسی‌ها برای این موجودیت قبلاً تعریف شده‌اند. 
  لطفاً موجودیت دیگری انتخاب کنید.
</div>
```

#### ب) غیرفعال کردن دکمه ذخیره
```html
<button type="submit" 
        :disabled="!selectedEntityId || availableViewsCount === 0"
        :class="(!selectedEntityId || availableViewsCount === 0) ? 
                'opacity-50 cursor-not-allowed' : 
                'hover:from-indigo-700 hover:to-purple-700'">
  ذخیره دسترسی
</button>
```

#### ج) به‌روزرسانی دکمه Reset
```html
<button type="reset" 
        @click="availableViewsCount = 0; selectedEntityId = ''; entityType = '';">
  پاک کردن فرم
</button>
```

---

## جریان کار (Workflow)

```
1. کاربر نوع موجودیت را انتخاب می‌کند (مثلاً "قسمت")
   ↓
2. لیست موجودیت‌ها نمایش داده می‌شود
   ↓
3. کاربر یک موجودیت مشخص را انتخاب می‌کند (مثلاً "قسمت HSE")
   ↓
4. درخواست AJAX به سرور ارسال می‌شود:
   GET /permissions/available-views/?entity_type=part&entity_id=5
   ↓
5. سرور:
   - تمام صفحات را دریافت می‌کند
   - صفحاتی که این قسمت به آن‌ها دسترسی دارد را می‌یابد
   - فقط صفحات بدون دسترسی را برمی‌گرداند
   ↓
6. لیست صفحات به‌روزرسانی می‌شود:
   - اگر صفحه‌ای موجود باشد: نمایش لیست
   - اگر صفحه‌ای موجود نباشد: نمایش پیغام + غیرفعال کردن دکمه
   ↓
7. کاربر صفحات مورد نظر را انتخاب و ذخیره می‌کند
```

---

## مثال‌های کاربردی

### مثال 1: صفحات موجود دارد
```
کاربر: قسمت "HSE" را انتخاب می‌کند
سرور: 15 صفحه از 50 صفحه قبلاً تعریف شده
نمایش: 35 صفحه باقی‌مانده در لیست
```

### مثال 2: همه صفحات تعریف شده
```
کاربر: کاربر "احمد رضایی" را انتخاب می‌کند
سرور: همه 50 صفحه قبلاً تعریف شده
نمایش: پیغام هشدار + دکمه ذخیره غیرفعال
```

### مثال 3: موجودیت جدید
```
کاربر: بخش جدید "امور اداری" را انتخاب می‌کند
سرور: هیچ دسترسی تعریف نشده
نمایش: همه 50 صفحه در لیست
```

---

## مزایای این قابلیت

### 1. بهبود تجربه کاربری
- ✅ کاربر فقط گزینه‌های مرتبط را می‌بیند
- ✅ زمان جستجو کاهش می‌یابد
- ✅ احتمال خطا کاهش می‌یابد

### 2. جلوگیری از خطا
- ✅ امکان ایجاد دسترسی تکراری وجود ندارد
- ✅ پیغام واضح در صورت عدم وجود صفحه موجود

### 3. بهینه‌سازی عملکرد
- ✅ فقط داده‌های ضروری نمایش داده می‌شوند
- ✅ لیست کوچک‌تر = سرعت بیشتر

### 4. قابلیت نگهداری
- ✅ کد تمیز و قابل فهم
- ✅ جداسازی منطق backend و frontend
- ✅ استفاده از AJAX برای تعامل بدون رفرش صفحه

---

## فایل‌های تغییر یافته

| فایل | نوع تغییر | توضیح |
|------|-----------|--------|
| `permissions/views.py` | ✚ اضافه | تابع `get_available_views` |
| `permissions/urls.py` | ✚ اضافه | مسیر `/available-views/` |
| `templates/permissions/manage_access.html` | ✎ ویرایش | افزودن JavaScript و UI جدید |

---

## تست‌های پیشنهادی

### 1. تست عملکرد پایه
- [ ] انتخاب موجودیتی که دسترسی ندارد → همه صفحات نمایش داده شوند
- [ ] انتخاب موجودیتی با چند دسترسی → فقط صفحات باقی‌مانده نمایش داده شوند
- [ ] انتخاب موجودیتی با همه دسترسی‌ها → پیغام هشدار نمایش داده شود

### 2. تست UI
- [ ] دکمه ذخیره غیرفعال شود وقتی صفحه‌ای موجود نیست
- [ ] پیغام هشدار به درستی نمایش داده شود
- [ ] لیست صفحات به‌روزرسانی شود بدون رفرش صفحه

### 3. تست Edge Cases
- [ ] تغییر سریع بین موجودیت‌ها
- [ ] خطای شبکه
- [ ] موجودیت نامعتبر

---

## نتیجه‌گیری
این قابلیت تجربه کاربری را به طور قابل توجهی بهبود می‌دهد و از ایجاد دسترسی‌های تکراری جلوگیری می‌کند. پیاده‌سازی با استفاده از AJAX باعث شده که فرآیند سریع و روان باشد.
