# 📸 Visual Guide: Leave Inbox Integration

## 🎯 Dashboard Inbox Widget

### Widget Header (Purple Gradient)
```
┌──────────────────────────────────────────────────────────┐
│ 📬  کارتابل شما                                    [2] │
│     درخواست‌های منتظر تأیید                             │
└──────────────────────────────────────────────────────────┘
```

### Replacement Approvals Section (Blue)
```
┌──────────────────────────────────────────────────────────┐
│ 👤 تأیید جایگزینی                                  [1]  │
├──────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────┐   │
│ │ محمد کاظمی          [استعلاجی]                   │   │
│ │ 📅 1403/08/15  ⏰ 08:00                           │   │
│ │                              [✅ تأیید] [❌ رد]   │   │
│ └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Manager Approvals Section (Purple)
```
┌──────────────────────────────────────────────────────────┐
│ 🎖️ تأیید نهایی مدیر                                [1]  │
├──────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────┐   │
│ │ علی احمدی           [استحقاقی]                   │   │
│ │ 📅 1403/08/16  ⏰ 09:00                           │   │
│ │                              [✅ تأیید] [❌ رد]   │   │
│ └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Reject Modal
```
┌────────────────────────────────────────────────────┐
│  ⚠️  رد درخواست مرخصی                            │
│                                                    │
│  دلیل رد درخواست:                                 │
│  ┌──────────────────────────────────────────────┐ │
│  │                                              │ │
│  │  لطفاً دلیل رد را توضیح دهید...            │ │
│  │                                              │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│              [🔴 تأیید رد]  [⚪ انصراف]          │
└────────────────────────────────────────────────────┘
```

### Footer Link
```
┌──────────────────────────────────────────────────────────┐
│      → مشاهده همه درخواست‌های مرخصی ←                   │
└──────────────────────────────────────────────────────────┘
```

---

## 🗂️ Sidebar Structure

### Before (Old Structure)
```
📊 داشبورد
👥 مدیریت پیمانکاران
   └─ داشبورد پیمانکاران
   └─ گزارش‌های کارکرد
   └─ مدیریت اطلاعات پایه
🛡️ واحد ایمنی (HSEC)
   └─ مدیریت ایمنی آتش‌نشانی
   └─ گزارشات آتش‌نشانی
   └─ مدیریت آنومالی
   └─ ...
```

### After (New Structure)
```
📊 داشبورد
👥 مدیریت پیمانکاران
   └─ داشبورد پیمانکاران
   └─ گزارش‌های کارکرد
   └─ مدیریت اطلاعات پایه
👥 واحد اداری ⭐ NEW
   └─ 👤 مدیریت پرسنل
   └─ 📅 مدیریت مرخصی
       ├─ ➕ درخواست مرخصی
       ├─ 📦 آرشیو مرخصی‌ها
       └─ ⚙️ مدیریت تأییدکنندگان
🛡️ واحد ایمنی (HSEC)
   └─ مدیریت ایمنی آتش‌نشانی
   └─ گزارشات آتش‌نشانی
   └─ مدیریت آنومالی
   └─ ...
```

---

## 🎨 Color Scheme

### Dashboard Widget:
- **Header Background:** Purple gradient (`#9333ea` → `#a855f7`)
- **Header Text:** White
- **Badge Counter:** White with 20% opacity background
- **Replacement Section:**
  - Badge: Blue (`bg-blue-100`, `text-blue-800`)
  - Icon: Blue (`text-blue-600`)
- **Manager Section:**
  - Badge: Purple (`bg-purple-100`, `text-purple-800`)
  - Icon: Purple (`text-purple-600`)
- **Approve Button:** Green (`bg-emerald-600`, hover: `bg-emerald-700`)
- **Reject Button:** Red (`bg-rose-600`, hover: `bg-rose-700`)
- **Leave Type Badge:** Amber (`bg-amber-100`, `text-amber-800`)

### Sidebar:
- **واحد اداری Icon:** Indigo (`text-indigo-600`)
- **مدیریت پرسنل Icon:** Teal (`text-teal-600`)
- **مدیریت مرخصی Icon:** Purple (`text-purple-600`)
- **درخواست مرخصی Icon:** Green (`text-green-600`)
- **آرشیو مرخصی‌ها Icon:** Blue (`text-blue-600`)
- **مدیریت تأییدکنندگان Icon:** Orange (`text-orange-600`)

---

## 🎬 User Flow Animations

### 1. Approve Request:
```
[Initial State]
┌────────────────────────────┐
│ علی احمدی   [✅] [❌]     │
└────────────────────────────┘
        ↓ Click Approve
[Confirmation Dialog]
┌────────────────────────────┐
│ آیا مطمئن هستید؟          │
│      [بله]  [خیر]         │
└────────────────────────────┘
        ↓ Click Yes
[Processing - AJAX]
        ↓
[Success]
┌────────────────────────────┐
│ ✅ درخواست تأیید شد       │ ← Notification
└────────────────────────────┘
[Row Fades Out]
┌────────────────────────────┐
│ علی احمدی   [✅] [❌]     │ ← Opacity: 0
└────────────────────────────┘
        ↓
[Row Removed]
```

### 2. Reject Request:
```
[Initial State]
┌────────────────────────────┐
│ علی احمدی   [✅] [❌]     │
└────────────────────────────┘
        ↓ Click Reject
[Modal Opens]
┌────────────────────────────┐
│ ⚠️ رد درخواست مرخصی      │
│ دلیل: [_______________]   │
│      [تأیید] [انصراف]     │
└────────────────────────────┘
        ↓ Enter Reason
[Type in textarea]
        ↓ Click Confirm
[Processing - AJAX]
        ↓
[Success]
┌────────────────────────────┐
│ ✅ درخواست رد شد          │ ← Notification
└────────────────────────────┘
[Modal Closes + Row Fades]
        ↓
[Row Removed]
```

---

## 📱 Responsive Behavior

### Desktop (> 1024px):
- Widget full width
- Two buttons side by side
- Modal centered

### Tablet (768px - 1024px):
- Widget full width
- Buttons slightly smaller
- Modal 90% width

### Mobile (< 768px):
- Widget full width
- Buttons stack vertically
- Modal full width
- Text sizes adjust

---

## 🔄 State Management

### Widget States:
1. **Empty State:** Widget hidden (not rendered)
2. **Has Pending:** Widget visible
3. **Loading (AJAX):** Button disabled, spinner optional
4. **Success:** Row animates out
5. **Error:** Error notification shows
6. **Last Item Removed:** Page reloads

### Modal States:
1. **Hidden:** `display: none`
2. **Open:** `display: block` with backdrop
3. **Submitting:** Buttons disabled
4. **Closed:** Animated fade-out

---

## 🎯 Permission Matrix

| Feature | Permission Required | Fallback |
|---------|-------------------|----------|
| Dashboard Widget | Automatic (based on role) | Hidden if no approvals |
| Replacement Section | `replacement_person == user` | Not shown |
| Manager Section | In `ApprovalHierarchy` | Not shown |
| Request Leave Link | `leave_request_create` | Hidden |
| Archive Link | `leave_archive_view` | Hidden |
| Manage Approvers | `is_superuser` | Hidden |
| Personnel Management | `personnel_management` | Hidden |

---

## 📊 Data Display Examples

### Leave Types with Badges:
- 🟡 استعلاجی (Sick Leave) - Amber
- 🟡 استحقاقی (Vacation) - Amber
- 🟡 بدون حقوق (Unpaid) - Amber
- 🟡 ساعتی (Hourly) - Amber

### Dates (Jalali Format):
- `1403/08/15` (displayed via `to_jalali` filter)
- Time: `08:00` or `--:--` if not set

### User Names:
- Full name if available: `محمد کاظمی`
- Username as fallback: `m.kazemi`

---

## ⚡ Performance Notes

### Optimization Applied:
- ✅ Limit 5 most recent per section
- ✅ `select_related()` to reduce queries
- ✅ `order_by('-created_at')` for chronological display
- ✅ Conditional rendering (only if data exists)
- ✅ Efficient Q objects for manager queries

### Query Count:
- **Without approvals:** 0 extra queries
- **With replacement approvals:** +1 query
- **With manager approvals:** +2 queries (ApprovalHierarchy + ShiftReport)
- **Total overhead:** ~3 queries maximum

---

## 🎉 User Experience Highlights

### ✨ What Makes It Great:
1. **No Extra Page:** Approvals right on dashboard
2. **Visual Clarity:** Color-coded sections and badges
3. **Quick Actions:** One-click approve/reject
4. **Smooth Animations:** Professional feel
5. **Instant Feedback:** Toast notifications
6. **Smart Reload:** Only when necessary
7. **Organized Sidebar:** Logical grouping
8. **Permission-Based:** Shows only what's relevant

### 🎯 User Goals Achieved:
- ✅ Quickly see pending tasks
- ✅ Act on requests without navigation
- ✅ Understand context at a glance
- ✅ Provide rejection reasons when needed
- ✅ Find leave features easily in sidebar

---

**📍 Current Status:** All features implemented and ready for testing! 🎊
