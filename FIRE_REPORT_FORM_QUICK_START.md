# Quick Start Guide - Fire Report Form

## 🚀 Getting Started

The new Fire Report form is now available at:
- **Create**: `/fire-reports/create/`
- **Edit**: `/fire-reports/edit/<id>/`

## 📋 How to Use

### Step 1: General Information (اطلاعات کلی)
1. Select **Shift** (شیفت)
2. Choose **Shift Operator** (اپراتور شیفت) - Searchable dropdown
3. Select **Firefighter** (آتش‌نشان) - Searchable dropdown

### Step 2: Incident Summary (خلاصه حوادث)
1. Enter incident counts:
   - Dispatch incidents (تعداد حوادث اعزام)
   - Personal incidents (تعداد حوادث پرسنلی)
   - Equipment incidents (تعداد حوادث تجهیزاتی)
   - Fire incidents (تعداد حوادث آتش‌سوزی)
2. Add optional notes in **Additional Notes** field

### Step 3: Vehicle Status Reports (گزارش وضعیت خودروها)

#### For Each Vehicle:

1. **Choose Vehicle Source** (منبع خودرو):
   - Click "خودروی شرکتی" for company vehicles
   - Click "خودروی پیمانکار" for contractor vehicles

2. **Select Vehicle** from dropdown:
   - For company vehicles: Equipment status loads automatically ⚡
   - Watch for the spinner icon while loading

3. **Fill Equipment Status** (10 types):
   - ✅ مناسب (Suitable) or ❌ نامناسب (Unsuitable)
   - Add descriptions in text areas
   - Disabled fields show: "برای این خودرو تعریف نشده است"

4. **Add More Vehicles**:
   - Click "افزودن خودروی جدید" button
   - New card appears with smooth animation

5. **Remove Vehicle**:
   - Click trash icon 🗑️ in card header
   - Card fades out gracefully

## 🎯 Tips & Tricks

### Searchable Dropdowns
- Start typing to search by name or personnel code
- Works for operators, firefighters, and vehicles

### Equipment Auto-Disable
- When you select a company vehicle, unavailable equipment auto-disables
- Grey background = not applicable to this vehicle
- This prevents filling unnecessary fields

### Keyboard Navigation
- Tab through fields naturally
- Enter/Return in dropdowns selects option
- Works perfectly with screen readers

### Dark Mode
- Automatically matches system preference
- All colors optimized for both light and dark themes

## ⚠️ Important Notes

### Required Fields
Fields marked with **<span style="color:red">*</span>** are required:
- Shift
- Shift Operator
- Firefighter
- Vehicle Source (for each vehicle)
- Vehicle Selection (for each vehicle)

### Minimum Requirements
- At least **1 vehicle** must be added
- Cannot remove the last vehicle

### API Integration
- Company vehicles trigger automatic equipment fetch
- Loading spinner shows during API call
- Error handling built-in (logs to console)

## 🐛 Troubleshooting

### Dropdown Not Working
1. Refresh the page
2. Check browser console for errors
3. Ensure jQuery and Select2 are loaded

### Equipment Fields Not Disabling
1. Make sure you selected a company vehicle (not contractor)
2. Check that API endpoint is accessible
3. Look for loading spinner - if it appears but fields don't update, check console

### Form Won't Submit
1. Check for validation errors (red messages)
2. Ensure all required fields are filled
3. At least one vehicle must be present

### Styling Issues
1. Clear browser cache
2. Ensure Tailwind CSS is loaded (check page source)
3. Check for conflicting CSS

## 🎨 Customization

### Colors
Edit the CSS in `report_form.html` `<style>` block:
- Primary: `indigo-600` → change to your brand color
- Success: `green-600`
- Danger: `red-600`

### Translations
All Persian text is inline in templates:
- `report_form.html`: Section headers and labels
- `vehicle_form_card.html`: Equipment labels

### Equipment Types
To add/remove equipment fields, edit:
1. `vehicle_form_card.html` - Template array
2. `models.py` - Add model fields
3. `forms.py` - Add form fields
4. API endpoint response in `views.py`

## 📱 Mobile Experience

The form is fully responsive:
- **Desktop**: 3-column grid for incidents, 3-column for equipment
- **Tablet**: 2-column layout
- **Mobile**: Single column, stacked layout

## ♿ Accessibility

- ✅ Proper ARIA labels
- ✅ Keyboard navigation
- ✅ Screen reader compatible
- ✅ Focus indicators
- ✅ Color contrast (WCAG AA)

## 🔒 Security

- ✅ CSRF protection
- ✅ Permission-based access
- ✅ Input validation (client & server)
- ✅ SQL injection prevention (Django ORM)

## 📊 Performance

- ⚡ Minimal JavaScript (Alpine.js ~15KB)
- ⚡ No jQuery in Alpine component (only for Select2)
- ⚡ Lazy API calls (only when needed)
- ⚡ Smooth animations (60fps)

## 🚀 Next Steps

1. **Test the form** thoroughly in your environment
2. **Customize colors** to match your brand
3. **Add validation rules** if needed
4. **Monitor user feedback** for improvements

---

**Need Help?** Check the full documentation in `FIRE_REPORT_FORM_IMPLEMENTATION.md`
