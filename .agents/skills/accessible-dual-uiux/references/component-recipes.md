# کدهای آماده و کامپوننت‌های نمونه برای سیستم UI/UX دومنظوره

## ۱. کامپوننت‌های رده ۱ (پرسنل خط مقدم / با سواد کم)

### ۱-۱. کارت انتخاب دوتایی/سه‌تایی بزرگ (جایگزین دراپ‌داون)
```html
<style>
  .big-choices { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin: 12px 0; }
  .big-choice-card {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    border: 2px solid #cbd5e1; border-radius: 16px; padding: 18px 12px; cursor: pointer;
    background: #fff; transition: all 0.2s ease; text-align: center; font-size: 17px; font-weight: 700;
  }
  .big-choice-card:active { transform: scale(0.97); }
  .big-choice-input:checked + .big-choice-card {
    border-color: #2563eb; background: #eff6ff; color: #1d4ed8; box-shadow: 0 0 0 3px rgba(37,99,235,0.2);
  }
  .big-choice-card .icon { font-size: 32px; margin-bottom: 6px; }
</style>

<div class="big-choices">
  <label>
    <input type="radio" name="gender" value="male" class="big-choice-input" style="display:none;" {% if data.gender == 'male' %}checked{% endif %}>
    <div class="big-choice-card">
      <span class="icon">👨</span>
      <span>مذکر</span>
    </div>
  </label>
  <label>
    <input type="radio" name="gender" value="female" class="big-choice-input" style="display:none;" {% if data.gender == 'female' %}checked{% endif %}>
    <div class="big-choice-card">
      <span class="icon">👩</span>
      <span>مونث</span>
    </div>
  </label>
</div>
```

### ۱-۲. دکمه چسبان پایین صفحه مخصوص موبایل (Sticky Mobile Action Bar)
```html
<style>
  .mobile-sticky-action {
    position: fixed; bottom: 0; left: 0; right: 0; background: #ffffff;
    border-top: 1px solid #e2e8f0; padding: 12px 16px; z-index: 50;
    box-shadow: 0 -8px 20px rgba(0,0,0,0.06); max-width: 600px; margin: 0 auto;
  }
  .btn-frontline-primary {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    width: 100%; min-height: 54px; font-size: 18px; font-weight: 800;
    background: #1d4ed8; color: #ffffff; border: none; border-radius: 14px; cursor: pointer;
  }
</style>

<div class="mobile-sticky-action">
  <button type="submit" class="btn-frontline-primary">
    <span>ثبت و مرحله بعد</span>
    <span>&larr;</span>
  </button>
</div>
```

---

## ۲. کامپوننت‌های رده ۲ (کارشناسان و مدیران)

### ۲-۱. نوار فیلتر و جستجوی پیشرفته
```html
<div class="filter-bar" style="display:flex; gap:10px; flex-wrap:wrap; background:#fff; padding:14px; border-radius:12px; border:1px solid #e2e8f0; margin-bottom:16px;">
  <div style="flex:1; min-width:220px;">
    <input type="text" placeholder="جستجو نام، کد پرسنلی یا کد ملی..." style="width:100%; padding:9px 12px; border:1px solid #cbd5e1; border-radius:8px; font-size:14px;">
  </div>
  <select style="padding:9px 12px; border:1px solid #cbd5e1; border-radius:8px; font-size:14px;">
    <option value="">همه وضعیت‌ها</option>
    <option value="pending">در انتظار تایید</option>
    <option value="approved">تایید شده</option>
    <option value="rejected">رد شده</option>
  </select>
  <button class="btn-admin-action" style="padding:9px 16px; background:#1e293b; color:#fff; border:none; border-radius:8px; font-size:14px; cursor:pointer;">
    فیلتر
  </button>
</div>
```

### ۲-۲. بج وضعیت استاندارد (Standard Status Badge)
```html
<style>
  .badge-status { display: inline-flex; align-items: center; gap: 5px; padding: 4px 10px; border-radius: 99px; font-size: 13px; font-weight: 700; }
  .badge-pending { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
  .badge-approved { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
  .badge-rejected { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
</style>

<span class="badge-status badge-pending">
  <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#d97706;"></span>
  در انتظار تایید
</span>
```
