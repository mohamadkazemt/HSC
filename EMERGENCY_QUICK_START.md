# Emergency Portal Quick Start Guide

## What Has Been Completed

### ✅ Backend Implementation (30% Complete)
1. **Forms**: `EmergencyPersonnelForm` for user management
2. **API Endpoints**: 20+ JSON APIs for AJAX operations
   - Medicines, Categories, Services, Equipment, Hospitals, Personnel
3. **URL Configuration**: All routes registered with permissions labels
4. **Management Command**: `setup_emergency_portal` to create groups

### ⏳ What Remains (Frontend & Integration - 70%)
1. **Templates**: Data management page, emergency login, base templates
2. **Views**: Login/logout, profile, enhanced dashboard views
3. **CSS/JS**: Emergency portal styling and AJAX handlers
4. **Main Sidebar**: Integration with existing navigation

## Immediate Next Steps

### Step 1: Setup Emergency Groups
```bash
cd /home/mohamadkazem/HSC
python manage.py setup_emergency_portal
```

This creates three Django groups:
- `EmergencyManager`
- `EmergencyDoctor`
- `EmergencyNurse`

### Step 2: Key Files to Create

#### Priority 1: Data Management Page
**File**: `templates/emergency_services/data_management.html`
- Tabbed interface for managing all emergency data
- AJAX-driven CRUD operations
- Uses APIs already created in `views.py`

#### Priority 2: Emergency Login
**Files**: 
- View: Add to `emergency_services/views.py`
- Template: `templates/emergency_services/emergency_login.html`
- URL: Add to `urls.py`

```python
# View to add to views.py
from django.contrib.auth import authenticate, login, logout

def emergency_login_view(request):
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
            messages.error(request, 'شما مجاز به ورود به پورتال اورژانس نیستید.')
    
    return render(request, 'emergency_services/emergency_login.html')

def emergency_logout_view(request):
    logout(request)
    return redirect('emergency_services:emergency_login')
```

#### Priority 3: Emergency Base Templates
**Files**:
- `templates/emergency_services/emergency_base.html`
- `templates/emergency_services/partials/emergency_sidebar.html`

These provide a separate UI for emergency personnel (no main site navigation).

### Step 3: Testing the Backend APIs

You can test the API endpoints immediately using curl or Postman:

```bash
# Test medicine list API
curl -H "Cookie: sessionid=YOUR_SESSION" \
  http://localhost:8000/emergency/api/medicines/

# Test personnel list API
curl -H "Cookie: sessionid=YOUR_SESSION" \
  http://localhost:8000/emergency/api/personnel/
```

## File Structure Reference

```
emergency_services/
├── forms.py              ✅ EmergencyPersonnelForm added
├── views.py              ✅ 20+ API endpoints added
├── urls.py               ✅ All routes registered
├── models.py             ✅ Existing (no changes needed)
├── management/
│   └── commands/
│       └── setup_emergency_portal.py  ✅ Created
└── templates/
    └── emergency_services/
        ├── data_management.html       ⏳ TO CREATE
        ├── emergency_login.html       ⏳ TO CREATE
        ├── emergency_base.html        ⏳ TO CREATE
        ├── emergency_profile.html     ⏳ TO CREATE
        └── partials/
            └── emergency_sidebar.html ⏳ TO CREATE
```

## API Endpoints Reference

### Medicines
- `GET /emergency/api/medicines/` - List all medicines
- `POST /emergency/api/medicines/save/` - Create/update medicine
- `POST /emergency/api/medicines/<id>/delete/` - Delete medicine

### Categories
- `GET /emergency/api/categories/` - List all categories
- `POST /emergency/api/categories/save/` - Create/update category
- `POST /emergency/api/categories/<id>/delete/` - Delete category

### Services
- `GET /emergency/api/services/` - List all services
- `POST /emergency/api/services/save/` - Create/update service
- `POST /emergency/api/services/<id>/delete/` - Delete service

### Equipment
- `GET /emergency/api/equipment/` - List all equipment
- `POST /emergency/api/equipment/save/` - Create/update equipment
- `POST /emergency/api/equipment/<id>/delete/` - Delete equipment

### Hospitals
- `GET /emergency/api/hospitals/` - List all hospitals
- `POST /emergency/api/hospitals/save/` - Create/update hospital
- `POST /emergency/api/hospitals/<id>/delete/` - Delete hospital

### Personnel
- `GET /emergency/api/personnel/` - List all emergency personnel
- `POST /emergency/api/personnel/save/` - Create/update personnel
- `POST /emergency/api/personnel/<id>/delete/` - Remove from emergency groups
- `GET /emergency/api/personnel/<id>/` - Get personnel details

## Sample AJAX Usage

```javascript
// Example: Load medicines data
$.get('/emergency/api/medicines/', function(response) {
    const medicines = response.data;
    medicines.forEach(med => {
        console.log(`${med.name}: ${med.quantity} available`);
    });
});

// Example: Save new medicine
$.ajax({
    url: '/emergency/api/medicines/save/',
    method: 'POST',
    data: {
        name: 'پاراستامول',
        category: 1,
        quantity: 100,
        expiry_date: '1404/12/29',
        critical_threshold: 20,
        is_active: true
    },
    headers: {
        'X-CSRFToken': getCookie('csrftoken')
    },
    success: function(response) {
        if (response.success) {
            console.log('Medicine saved!');
        }
    }
});
```

## Permission Configuration

After creating emergency users, you'll need to assign permissions. The system uses your existing `permissions` app.

Example: Grant a user access to the emergency dashboard:

```python
from permissions.models import UserPermission
from django.contrib.auth.models import User

user = User.objects.get(username='doctor_ali')
UserPermission.objects.create(
    user=user,
    view_name='dashboard',
    can_view=True,
    can_add=False,
    can_edit=False,
    can_delete=False
)
```

## Color Scheme

Use these CSS variables consistently:
- `--emergency-red: #dc3545` - Critical alerts, emergencies
- `--emergency-green: #28a745` - Good status, success
- `--emergency-blue: #007bff` - Information, actions
- `--emergency-warning: #ffc107` - Warnings, attention needed

## Icon Reference (FontAwesome)

- Dashboard: `fas fa-tachometer-alt`
- Ambulance/Emergency: `fas fa-ambulance`
- Patient: `fas fa-user-injured`
- Medicine: `fas fa-pills`
- Hospital: `fas fa-hospital`
- Equipment: `fas fa-heartbeat`
- Doctor: `fas fa-user-md`
- Nurse: `fas fa-user-nurse`
- Add: `fas fa-plus-circle`
- Edit: `fas fa-edit`
- Delete: `fas fa-trash-alt`

## Troubleshooting

### API returns 403 Forbidden
- Check user permissions with the permissions app
- Verify user is logged in
- Ensure CSRF token is included in POST requests

### Groups not found
- Run `python manage.py setup_emergency_portal`
- Check with `python manage.py shell`:
  ```python
  from django.contrib.auth.models import Group
  Group.objects.filter(name__contains='Emergency')
  ```

### Templates not loading
- Check `TEMPLATES` setting in settings.py
- Verify template directory structure
- Run `python manage.py collectstatic` if in production

## Support

For detailed implementation guidance, see:
- `EMERGENCY_PORTAL_IMPLEMENTATION.md` - Full specification
- `emergency_services/views.py` - API implementation examples
- `emergency_services/forms.py` - Form examples

---
**Created**: 2025-11-01  
**Status**: Backend 30% Complete, Frontend Pending  
**Next Sprint**: Create data_management.html template
