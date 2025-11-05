# Emergency Portal Implementation Guide

## Overview
This document provides a complete implementation guide for the Emergency Services Portal with frontend admin panel and user management integration.

## Completed Tasks ✅

### 1. Emergency Personnel User Management Forms
- ✅ Created `EmergencyPersonnelForm` in `emergency_services/forms.py`
- ✅ Supports user creation and editing with role assignment
- ✅ Three roles: EmergencyManager, EmergencyDoctor, EmergencyNurse
- ✅ Password validation and group management

### 2. API Views for Data Management
- ✅ Created comprehensive JSON API endpoints in `views.py`:
  - Medicines: list, save, delete
  - Categories: list, save, delete
  - Services: list, save, delete
  - Equipment: list, save, delete
  - Hospitals: list, save, delete
  - Personnel: list, save, delete, detail
- ✅ All APIs support search filtering
- ✅ Proper error handling and validation
- ✅ Persian date conversion for datetime fields

### 3. URL Configuration
- ✅ Added all API endpoint URLs
- ✅ Added data_management URL
- ✅ All URLs registered with URLS_WITH_LABELS for permissions

## Remaining Implementation Tasks

### 1. Data Management Page Template
**File**: `templates/emergency_services/data_management.html`

**Requirements**:
- Card-based tabbed interface
- 6 Tabs: Medicines | Categories | Services | Equipment | Hospitals | Personnel
- Each tab contains:
  - "Add New" button (opens modal)
  - Searchable data table
  - Edit/Delete action buttons
- AJAX-driven (no page reloads)
- Use Select2 for dropdowns
- Jalali DateTimePicker for date fields

**Key Features**:
```javascript
// Tab structure
<ul class="nav nav-tabs">
  <li class="nav-item">
    <a class="nav-link active" data-tab="medicines">داروها</a>
  </li>
  // ... other tabs
</ul>

// Each tab has:
- Search bar with live filtering
- Data table with DataTables.js
- Modal forms for add/edit operations
- AJAX submission handlers
```

### 2. Emergency Personnel Login System
**Files**:
- `views.py`: Add `emergency_login`, `emergency_logout` views
- `templates/emergency_services/emergency_login.html`

**Requirements**:
- Separate login page at `/emergency/login/`
- Simple, focused design (no main site navigation)
- Custom authentication that checks for emergency groups
- Redirect to emergency dashboard after login
- Session management for emergency portal

**View Logic**:
```python
@login_required
def emergency_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user and user.groups.filter(
            name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse']
        ).exists():
            login(request, user)
            return redirect('emergency_services:dashboard')
        else:
            messages.error(request, 'شما مجاز به ورود نیستید.')
    
    return render(request, 'emergency_services/emergency_login.html')
```

### 3. Emergency Portal Base Templates
**Files**:
- `templates/emergency_services/emergency_base.html`
- `templates/emergency_services/partials/emergency_sidebar.html`

**Requirements**:
- Separate base template for emergency portal
- Limited sidebar menu:
  - داشبورد اورژانس
  - ثبت مراجعه جدید
  - لیست مراجعات
  - موجودی داروها
  - تجهیزات
  - پروفایل من
- Role-based menu item visibility using `{% if user.groups.filter(name='EmergencyManager').exists %}`
- Medical-themed icons (FontAwesome medical icons)
- Color scheme: Red (#dc3545) for emergencies, Green (#28a745) for good status

**Sidebar Structure**:
```django
{% load permission_tags %}

<aside class="emergency-sidebar">
    <div class="logo">
        <i class="fas fa-ambulance"></i>
        <h3>پورتال اورژانس</h3>
    </div>
    
    <nav class="menu">
        {% if user|has_permission:'emergency_services:dashboard' %}
        <a href="{% url 'emergency_services:dashboard' %}">
            <i class="fas fa-tachometer-alt"></i>
            <span>داشبورد</span>
        </a>
        {% endif %}
        
        {% if user|has_permission:'emergency_services:create_visit' %}
        <a href="{% url 'emergency_services:create_visit' %}">
            <i class="fas fa-plus-circle"></i>
            <span>ثبت مراجعه</span>
        </a>
        {% endif %}
        
        // ... other menu items
    </nav>
</aside>
```

### 4. Enhanced Dashboard for Portal Users
**File**: `templates/emergency_services/dashboard.html`

**Requirements**:
- Detect if user is emergency personnel (check groups)
- Show different stats based on role:
  - **Doctor**: Patients awaiting diagnosis, recent visits
  - **Nurse**: Medicine inventory alerts, equipment status
  - **Manager**: Full overview with all statistics
- Color-coded stat cards
- Real-time alerts section
- Quick action buttons

**Role Detection**:
```django
{% if user.groups.filter(name='EmergencyDoctor').exists %}
    <!-- Doctor-specific dashboard -->
{% elif user.groups.filter(name='EmergencyNurse').exists %}
    <!-- Nurse-specific dashboard -->
{% elif user.groups.filter(name='EmergencyManager').exists %}
    <!-- Manager-specific dashboard -->
{% else %}
    <!-- Admin dashboard (full access) -->
{% endif %}
```

### 5. Multi-Card Visit Form
**File**: `templates/emergency_services/visit_form.html`

**Requirements**:
- Replace single-form layout with multi-step card design
- 5 Sections:
  1. **Patient Selection** (company/contractor radio with conditional dropdowns)
  2. **Visit Information** (reason, time, datetime picker)
  3. **Medical Services** (checkbox list)
  4. **Medicines** (dynamic formset with Select2)
  5. **Hospital Information** (optional, conditional on hospitalization)

**Card Structure**:
```html
<div class="visit-form-cards">
    <div class="card">
        <div class="card-header bg-primary text-white">
            <i class="fas fa-user-injured"></i>
            اطلاعات بیمار
        </div>
        <div class="card-body">
            <!-- Patient selection fields -->
        </div>
    </div>
    
    <div class="card">
        <div class="card-header bg-info text-white">
            <i class="fas fa-notes-medical"></i>
            اطلاعات مراجعه
        </div>
        <div class="card-body">
            <!-- Visit details -->
        </div>
    </div>
    
    <!-- ... more cards -->
</div>
```

### 6. Emergency Personnel Profile Page
**Files**:
- `views.py`: Add `emergency_profile`, `emergency_change_password` views
- `templates/emergency_services/emergency_profile.html`

**Requirements**:
- Display user information (read-only: name, username, role)
- Password change form
- Recent activity log (their visits, actions)
- Profile statistics (visits logged, medicines dispensed, etc.)

**View Logic**:
```python
@login_required
def emergency_profile(request):
    user = request.user
    # Get user's emergency group
    emergency_groups = user.groups.filter(
        name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse']
    )
    
    # Get user's recent activities
    recent_visits = MedicalVisit.objects.filter(
        created_by__user=user
    ).order_by('-created_at')[:10]
    
    context = {
        'user': user,
        'role': emergency_groups.first() if emergency_groups.exists() else None,
        'recent_visits': recent_visits,
    }
    return render(request, 'emergency_services/emergency_profile.html', context)
```

### 7. Main Sidebar Update
**File**: `templates/partials/sidebar.html`

**Requirements**:
- Add "مدیریت اورژانس" menu item
- Sub-menus with permission checks:
  ```django
  {% if user|has_permission:'emergency_services:dashboard' %}
  <li class="menu-item">
      <a href="#" class="has-submenu">
          <i class="fas fa-ambulance"></i>
          <span>مدیریت اورژانس</span>
      </a>
      <ul class="submenu">
          {% if user|has_permission:'emergency_services:dashboard' %}
          <li><a href="{% url 'emergency_services:dashboard' %}">داشبورد اورژانس</a></li>
          {% endif %}
          
          {% if user|has_permission:'emergency_services:data_management' %}
          <li><a href="{% url 'emergency_services:data_management' %}">مدیریت داده‌ها</a></li>
          {% endif %}
          
          {% if user|has_permission:'emergency_services:create_visit' %}
          <li><a href="{% url 'emergency_services:create_visit' %}">ثبت مراجعه جدید</a></li>
          {% endif %}
          
          {% if user|has_permission:'emergency_services:visit_list' %}
          <li><a href="{% url 'emergency_services:visit_list' %}">آرشیو مراجعات</a></li>
          {% endif %}
      </ul>
  </li>
  {% endif %}
  ```

## CSS/JS Requirements

### CSS (Add to static files)
```css
/* Emergency Portal Theme Colors */
:root {
    --emergency-red: #dc3545;
    --emergency-green: #28a745;
    --emergency-blue: #007bff;
    --emergency-warning: #ffc107;
}

/* Card Design */
.card {
    border: none;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.card-header {
    border-radius: 10px 10px 0 0;
    padding: 15px 20px;
    font-weight: 600;
}

/* Status Badges */
.badge-critical {
    background-color: var(--emergency-red);
}

.badge-good {
    background-color: var(--emergency-green);
}

.badge-warning {
    background-color: var(--emergency-warning);
}

/* Emergency Sidebar */
.emergency-sidebar {
    background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
    color: white;
    min-height: 100vh;
}
```

### JavaScript (AJAX Operations)
```javascript
// Generic AJAX function for data management
function saveData(endpoint, formData, successCallback) {
    $.ajax({
        url: endpoint,
        method: 'POST',
        data: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                successCallback();
                $('#dataModal').modal('hide');
                loadTableData(); // Refresh table
                showAlert('success', 'عملیات با موفقیت انجام شد');
            } else {
                showErrors(response.errors);
            }
        },
        error: function() {
            showAlert('error', 'خطا در ارتباط با سرور');
        }
    });
}

// Initialize Select2 for all selects
$(document).ready(function() {
    $('.select2').select2({
        dir: 'rtl',
        language: 'fa'
    });
});

// Initialize Jalali DateTimePicker
$(document).ready(function() {
    $('.jalali-datetime').persianDatepicker({
        format: 'YYYY/MM/DD HH:mm:ss',
        timePicker: {
            enabled: true
        }
    });
});
```

## Database Migration Notes

### Create Emergency Groups
Run this management command or create via Django shell:

```python
from django.contrib.auth.models import Group

# Create emergency groups if they don't exist
groups = ['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse']
for group_name in groups:
    Group.objects.get_or_create(name=group_name)
```

### Permission Setup
For each emergency personnel group, assign appropriate permissions using your permissions system:

```python
from permissions.models import UserPermission
from django.contrib.auth.models import Group, User

# Example: Grant dashboard access to all emergency groups
emergency_groups = Group.objects.filter(
    name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse']
)

for group in emergency_groups:
    for user in group.user_set.all():
        UserPermission.objects.update_or_create(
            user=user,
            view_name='dashboard',
            defaults={
                'can_view': True,
                'can_add': False,
                'can_edit': False,
                'can_delete': False
            }
        )
```

## Testing Checklist

- [ ] Create test emergency users (manager, doctor, nurse)
- [ ] Test login at /emergency/login/
- [ ] Verify role-based dashboard views
- [ ] Test data management AJAX operations
- [ ] Test visit form multi-card layout
- [ ] Verify permission-based menu visibility
- [ ] Test profile page and password change
- [ ] Test medicine inventory alerts
- [ ] Test equipment calibration alerts
- [ ] Verify Persian date conversions

## Deployment Notes

1. **Static Files**: Run `python manage.py collectstatic`
2. **Migrations**: Run `python manage.py migrate`
3. **Create Groups**: Run the group creation script
4. **Assign Permissions**: Use Django admin or create management command
5. **Test Emergency Login**: Create at least one test user per role

## Security Considerations

1. **Role Verification**: Always check user groups in views
2. **Permission Decorators**: Use `@permission_required` on all views
3. **CSRF Protection**: Ensure all AJAX POSTs include CSRF token
4. **Password Strength**: Consider adding password validators
5. **Session Security**: Use secure session settings in production

## Support and Maintenance

For questions or issues:
1. Check logs in `/var/log/django/`
2. Verify permissions in Django admin
3. Test API endpoints with Postman
4. Review browser console for JavaScript errors

---

**Implementation Status**: 30% Complete
**Last Updated**: 2025-11-01
**Developer**: HSC Emergency Portal Team
