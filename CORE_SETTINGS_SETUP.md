# Core Settings Module - Quick Setup Guide

## Prerequisites
Ensure the following are in place:
1. Django development server running
2. Database migrations are up to date
3. You have staff/admin user credentials
4. Models exist in BaseInfo app (they do)

## Step 1: Run the Development Server
```bash
cd /home/mohamadkazem/HSC
python manage.py runserver
```

## Step 2: Access the Base Settings Page
1. Log in as a staff member or admin
2. Click on **"تنظیمات پایه"** (Base Settings) in the sidebar under the Settings section
3. Or navigate directly to: `http://localhost:8000/core/settings/base/`

## Step 3: Test Each Tab

### Tab 1: Mining Machines (دستگاه‌های معدنی)
**Test Cascading Dropdown:**
1. Click "افزودن دستگاه جدید" (Add New Machine)
2. Select a Work Group (گروه کاری)
3. Watch the Machine Type dropdown automatically populate
4. Change ownership to "پیمانکار" (Contractor)
5. Watch the Contractor dropdown appear
6. Fill in Workshop Code
7. Click Save

**Test Toggle Switch:**
1. Find a machine in the table
2. Click the toggle switch to activate/deactivate
3. The change should happen immediately via AJAX

**Test Search:**
1. Type in the search box
2. Table should filter in real-time (300ms debounce)

### Tab 2: Blocks (بلوک‌ها)
**Test Color-Coded Badges:**
1. Click "افزودن بلوک جدید" (Add New Block)
2. Fill in Block Name
3. Select different types and statuses
4. Save and observe colored badges in the table
5. Try: "باطله" (Waste - gray), "سنگ پرعیار" (Ore - green), "ترکیبی" (Mixed - blue)

### Tab 3: Dumps (دمپ‌ها)
1. Click "افزودن مورد جدید" (Add New Item)
2. Enter dump name and location
3. Select mineral type (if available)
4. Save

### Tab 4: Emergency Vehicles (خودروهای امدادی)
**Test Jalali Date Picker:**
1. Click "افزودن خودرو جدید" (Add New Vehicle)
2. Click on any date field (Last Maintenance, Next Maintenance, Insurance Expiry)
3. A Persian calendar should appear
4. Select a date
5. Fill in other required fields:
   - Workshop Code (کد کارگاهی)
   - Vehicle Type (نوع خودرو)
   - License Plate (پلاک)
   - Model (مدل)
   - Manufacture Year (سال ساخت)

**Test Equipment Checklist:**
1. Scroll down in the vehicle modal
2. See 10 checkboxes for equipment
3. Check/uncheck various equipment items
4. Save and verify

### Tab 5: Mineral Types (انواع سنگ)
1. Click "افزودن مورد جدید"
2. Enter name (e.g., "طلا", "مس", "آهن")
3. Add description
4. Save

### Tab 6: Work Groups (گروه‌های کاری)
1. Click "افزودن مورد جدید"
2. Enter name (e.g., "حفاری", "بارگیری", "حمل و نقل")
3. Add description
4. Save

### Tab 7: Machine Types (نوع دستگاه)
1. Click "افزودن مورد جدید"
2. Enter name (e.g., "بلدوزر", "لودر", "کامیون")
3. Select associated work group
4. Add description
5. Save

## Step 4: Test Delete Functionality
1. Click "حذف" (Delete) button on any row
2. Confirmation modal should appear
3. Click "حذف" (Delete) to confirm or "انصراف" (Cancel) to abort

## Step 5: Test Edit Functionality
1. Click "ویرایش" (Edit) button on any row
2. Modal should open with pre-filled data
3. Modify some fields
4. Click "ذخیره" (Save)
5. Table should refresh with updated data

## Step 6: Test Responsive Design
1. Resize browser window to mobile size
2. Tables should scroll horizontally if needed
3. Modals should be responsive
4. Sidebar should collapse on mobile

## Step 7: Test Dark Mode (if enabled)
1. Toggle dark mode in your system/browser
2. All components should adapt to dark theme
3. Text should remain readable
4. Colors should adjust appropriately

## Troubleshooting

### Issue: "Page not found" error
**Solution**: Make sure the core app URLs are included in the main project urls.py
```python
# In HSC/urls.py or HSCprojects/urls.py
urlpatterns = [
    # ... other patterns ...
    path('core/', include('core.urls')),
]
```

### Issue: Jalali datepicker not appearing
**Solution**: Check browser console for JavaScript errors. The datepicker loads from CDN.

### Issue: API returns 500 error
**Solution**: Check Django logs. Likely a model relationship issue. Ensure all foreign keys are properly set.

### Issue: Sidebar menu item not showing
**Solution**: 
1. Clear browser cache
2. Ensure you're logged in as staff member
3. Check template syntax in sidebar.html

### Issue: Cascading dropdown not working
**Solution**:
1. Check browser console for network errors
2. Verify `/core/api/machine-types-by-workgroup/<id>/` endpoint is accessible
3. Ensure JavaScript is enabled

## Common Errors and Fixes

### CSRF Token Error
If you get CSRF token errors on POST/PUT/DELETE:
```python
# In settings.py, add:
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']
```

### Foreign Key Constraint Violation
When deleting items with relationships:
```python
# In models.py, ensure proper on_delete behavior:
# SET_NULL for optional relationships
# CASCADE for dependent records
# PROTECT to prevent deletion if relationships exist
```

## Sample Test Data

### Create some work groups:
- "حفاری" (Drilling)
- "بارگیری" (Loading)
- "حمل و نقل" (Transportation)
- "تعمیر و نگهداری" (Maintenance)

### Create some machine types:
- "بلدوزر" (Bulldozer) - Work Group: حفاری
- "لودر" (Loader) - Work Group: بارگیری
- "کامیون معدن" (Mining Truck) - Work Group: حمل و نقل

### Create some mineral types:
- "طلا" (Gold)
- "مس" (Copper)
- "آهن" (Iron)
- "سنگ آهک" (Limestone)

## Performance Tips
1. For large datasets (1000+ records), consider adding pagination
2. Add database indexes on frequently searched fields
3. Use `select_related()` in views to reduce database queries (already implemented)
4. Enable Django's database query logging to identify slow queries

## Security Checklist
- ✅ All views require `@staff_member_required` decorator
- ✅ CSRF protection on all forms
- ✅ Input validation via Django models
- ✅ No raw SQL queries (using Django ORM)
- ⚠️ Consider adding rate limiting for API endpoints
- ⚠️ Consider adding audit logging for sensitive operations

## Next Steps
Once basic testing is complete:
1. Add sample data for all models
2. Test with realistic datasets
3. Get feedback from actual users
4. Consider implementing pagination
5. Add export functionality if needed
6. Implement audit trail if required
7. Add unit tests for API endpoints
8. Add integration tests for frontend interactions

## Support
For issues or questions:
1. Check Django logs: `logs/` directory
2. Check browser console for JavaScript errors
3. Review `CORE_SETTINGS_IMPLEMENTATION.md` for detailed documentation
