# 🎯 Leave Inbox Integration & Sidebar Reorganization - Complete

## 📋 Overview
Successfully integrated the Leave Approval Inbox into the main dashboard and reorganized the sidebar with a new HR/Admin Unit section.

**Date:** November 5, 2025  
**Status:** ✅ Complete and Ready for Testing

---

## ✨ Part 1: Inbox Integration into Dashboard

### 1️⃣ Backend Changes (`dashboard/views.py`)

#### Added Leave Inbox Queries:
```python
# Import models
from leave_reports.models import ShiftReport, ApprovalHierarchy
from django.db.models import Q

# Fetch pending replacement approvals
pending_replacement_approvals = ShiftReport.objects.filter(
    replacement_person=request.user,
    status='pending_replacement'
).select_related('user', 'user__userprofile').order_by('-created_at')[:5]

# Fetch pending manager approvals
if hasattr(request.user, 'userprofile'):
    managed_sections = ApprovalHierarchy.objects.filter(
        approver=request.user.userprofile
    ).values_list('section_id', flat=True)
    
    managed_parts = ApprovalHierarchy.objects.filter(
        approver=request.user.userprofile
    ).values_list('part_id', flat=True)
    
    pending_manager_approvals = ShiftReport.objects.filter(
        Q(user__userprofile__section_id__in=managed_sections) |
        Q(user__userprofile__part_id__in=managed_parts),
        status='pending_approval'
    ).select_related('user', 'user__userprofile').order_by('-created_at')[:5]
```

#### Context Variables Added:
- `pending_replacement_approvals` - درخواست‌های منتظر تأیید جایگزین
- `pending_manager_approvals` - درخواست‌های منتظر تأیید مدیر

---

### 2️⃣ Frontend Changes (`templates/dashboard/dashboard.html`)

#### Beautiful Inbox Widget Features:
✅ **Conditional Display** - Only shows when there are pending requests  
✅ **Gradient Header** - Purple gradient with inbox icon  
✅ **Badge Counter** - Shows total pending count  
✅ **Two Sections:**
   - 🔵 Replacement Approvals (تأیید جایگزینی)
   - 🟣 Manager Approvals (تأیید نهایی مدیر)

#### Each Request Row Includes:
- 👤 Requester's full name
- 🏷️ Leave type badge (استعلاجی, استحقاقی, etc.)
- 📅 Leave date (Jalali calendar)
- ⏰ Leave time
- ✅ Approve button (green)
- ❌ Reject button (red)

#### Modern Reject Modal:
- ⚠️ Warning icon and title
- 📝 Textarea for rejection reason
- 🔴 Confirm button
- ⚪ Cancel button
- Escape key to close

#### View All Link:
- Direct link to full leave archive
- Smooth hover animation

---

### 3️⃣ AJAX Functionality (`extra_js` block)

#### Implemented Functions:

**`approveReplacement(leaveId)`**
- Sends POST to `/leave_reports/approve-replacement/{id}/`
- Confirmation dialog before action
- Animates row removal on success
- Shows success/error notification
- Reloads page if no more requests

**`approveManager(leaveId)`**
- Sends POST to `/leave_reports/approve-manager/{id}/`
- Confirmation dialog
- Animated row removal
- Success/error notifications
- Auto-reload when empty

**`showRejectModal(leaveId, type)`**
- Opens modal for rejection
- Stores leave ID and type (replacement/manager)
- Clears previous reason text

**`closeRejectModal()`**
- Closes modal
- Resets state variables

**`confirmReject()`**
- Validates rejection reason
- Sends POST to appropriate endpoint:
  - `/leave_reports/reject-replacement/{id}/`
  - `/leave_reports/reject-manager/{id}/`
- Includes rejection reason in request body
- Animates row removal
- Shows notifications

**`showNotification(message, type)`**
- Beautiful toast notification
- Green for success, red for error
- Auto-fades after 3 seconds
- Centered at top of screen

**Helper Functions:**
- `getCookie(name)` - Gets CSRF token
- Escape key listener for modal

---

## 🗂️ Part 2: Sidebar Reorganization

### New "HR / Admin Unit" (واحد اداری) Section

#### Location in Sidebar:
Added before "Safety Unit (HSEC)" section

#### Main Menu Features:
- 👥 Users/Admin icon
- Collapsible with Alpine.js (`x-data="{ openHR: false }"`)
- Only visible for internal users (not contractors/employees)

#### Sub-menus:

**1. مدیریت پرسنل (Personnel Management)**
- Icon: Multi-user management icon
- Permission: `personnel_management`
- Link: `#` (placeholder for future implementation)
- Purpose: View, edit, and add company personnel

**2. مدیریت مرخصی (Leave Management)** - Nested submenu
- Icon: Calendar with checkmark
- Collapsible with `openLeave` state

**Leave Management Sub-items:**

a) **درخواست مرخصی (Request Leave)**
   - Icon: Plus/Add icon (green)
   - URL: `{% url 'leave_reports:request_leave' %}`
   - Permission: `leave_request_create`

b) **آرشیو مرخصی‌ها (Leave Archive)**
   - Icon: Archive box (blue)
   - URL: `{% url 'leave_reports:leave_archive' %}`
   - Permission: `leave_archive_view`

c) **مدیریت تأییدکنندگان (Manage Approvers)**
   - Icon: Settings/Cog (orange)
   - URL: `{% url 'leave_reports:manage_approvers' %}`
   - Permission: `is_superuser` only

---

## 🎨 Design Highlights

### Dashboard Inbox Widget:
- **Colors:**
  - Purple gradient header (`from-purple-600 to-purple-500`)
  - Blue badges for replacement section
  - Purple badges for manager section
  - Green approve buttons
  - Red reject buttons

- **Animations:**
  - Fade-out and slide-left on row removal
  - Smooth hover effects on all buttons
  - Modal backdrop transition

- **Responsive:**
  - Flexbox layout
  - Mobile-friendly buttons
  - Proper spacing and padding

### Sidebar Additions:
- **Consistent Icons:** Heroicons v2.0
- **Color Coding:**
  - Indigo: Main HR/Admin Unit icon
  - Teal: Personnel management
  - Purple: Leave management
  - Green: Create/Add actions
  - Blue: Archive/View actions
  - Orange: Settings/Admin actions

---

## 📊 Data Flow

### Request Approval Flow:
1. User views dashboard
2. Django queries pending approvals based on user role
3. Widget renders if approvals exist
4. User clicks "Approve" or "Reject"
5. JavaScript sends AJAX request
6. Backend validates and processes
7. JSON response returns
8. Row animates and removes
9. Success notification displays
10. Page reloads if no more requests

### Permission Checks:
- **Replacement Approvals:** `replacement_person == request.user`
- **Manager Approvals:** User's profile linked in `ApprovalHierarchy`
- **Sidebar Items:** Django template tags `check_permission`

---

## 🔧 Files Modified

### Backend:
- ✅ `/home/mohamadkazem/HSC/dashboard/views.py`
  - Added leave inbox queries (lines ~35-55)
  - Updated context dictionary

### Frontend:
- ✅ `/home/mohamadkazem/HSC/templates/dashboard/dashboard.html`
  - Added inbox widget (lines ~25-180)
  - Added reject modal (lines ~181-205)
  - Added JavaScript functions (extra_js block, ~200 lines)

- ✅ `/home/mohamadkazem/HSC/templates/partials/sidebar.html`
  - Added HR/Admin Unit section (lines ~179-280)
  - Nested Leave Management submenu

---

## ✅ Testing Checklist

### Dashboard Inbox:
- [ ] Widget appears only when user has pending approvals
- [ ] Replacement section shows for designated replacements
- [ ] Manager section shows for section/part managers
- [ ] Badge counter shows correct total
- [ ] Jalali dates display correctly
- [ ] Approve buttons work via AJAX
- [ ] Reject modal opens correctly
- [ ] Reject modal validates reason field
- [ ] Reject button sends reason to backend
- [ ] Rows animate and remove on success
- [ ] Success notifications display
- [ ] Error notifications display
- [ ] Page reloads when section becomes empty
- [ ] "View All" link works

### Sidebar:
- [ ] HR/Admin Unit menu appears for internal users
- [ ] HR/Admin Unit menu hidden for contractors/employees
- [ ] Menu expands/collapses smoothly
- [ ] Personnel Management link appears with permission
- [ ] Leave Management submenu expands
- [ ] Request Leave link appears with permission
- [ ] Archive link appears with permission
- [ ] Manage Approvers link only for superuser
- [ ] All icons render correctly
- [ ] Hover effects work
- [ ] Active state highlights current page

---

## 🚀 Next Steps

### Required Actions:
1. **Define Permissions:**
   - Go to admin panel → Permissions
   - Create: `leave_request_create`
   - Create: `leave_archive_view`
   - Create: `personnel_management`
   - Assign to appropriate roles

2. **Test Complete Workflow:**
   - Login as Employee → Create leave request
   - Login as Replacement → See in dashboard → Approve
   - Login as Manager → See in dashboard → Approve/Reject
   - Verify status changes and timeline

3. **Implement Personnel Management:**
   - Create view for `/hr/personnel/`
   - Build CRUD interface for UserProfile
   - Link from sidebar

### Optional Enhancements:
- [ ] Add notification system (email/SMS)
- [ ] Add real-time updates (WebSocket)
- [ ] Add approval statistics to widget
- [ ] Add quick filters to inbox widget
- [ ] Add bulk approve/reject functionality

---

## 📝 API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/leave_reports/approve-replacement/{id}/` | POST | Approve as replacement |
| `/leave_reports/reject-replacement/{id}/` | POST | Reject as replacement |
| `/leave_reports/approve-manager/{id}/` | POST | Approve as manager |
| `/leave_reports/reject-manager/{id}/` | POST | Reject as manager |
| `/leave_reports/request/` | GET | Request leave form |
| `/leave_reports/archive/` | GET | Leave archive |
| `/leave_reports/manage-approvers/` | GET | Manage approvers |

---

## 🎉 Summary

**✅ All Requirements Implemented:**
- ✅ Leave inbox integrated into main dashboard
- ✅ Beautiful, interactive widget with AJAX
- ✅ Two-section layout (replacement + manager)
- ✅ Approve/Reject with animations
- ✅ Reject modal with reason field
- ✅ Success/error notifications
- ✅ New HR/Admin Unit in sidebar
- ✅ Leave Management submenu with 3 items
- ✅ Permission-based visibility
- ✅ Consistent design and icons

**🎯 Result:**
Users now have immediate access to pending leave approvals on their dashboard. The workflow is streamlined - no need to navigate to a separate page. The sidebar is better organized with a dedicated HR/Admin section that logically groups personnel and leave management.

**⚡ Performance:**
- Limited to 5 most recent requests per section
- Efficient queries with `select_related()`
- Smooth animations with CSS transitions
- No page reloads except when necessary

---

## 🆘 Troubleshooting

### Issue: Widget Not Appearing
**Solution:** Check user has pending approvals. Query database:
```python
ShiftReport.objects.filter(
    replacement_person=request.user,
    status='pending_replacement'
).count()
```

### Issue: AJAX Buttons Not Working
**Solution:** 
1. Check browser console for JavaScript errors
2. Verify CSRF token is present
3. Check leave_reports URLs are configured
4. Verify user permissions

### Issue: Sidebar Menu Not Expanding
**Solution:**
1. Check Alpine.js is loaded
2. Verify `x-data` and `x-show` directives
3. Check console for JavaScript errors

---

**🎊 Implementation Complete! Ready for production testing.**
