# Testing Checklist - Fire Report Form ✅

## Pre-Testing Setup

### 1. Environment Check
- [ ] Django server is running
- [ ] Database migrations are up to date
- [ ] Static files are collected (if in production)
- [ ] Browser console is open (F12)

### 2. Data Prerequisites
- [ ] At least 2 active company vehicles exist in database
- [ ] At least 1 contractor vehicle exists in database
- [ ] Users with "آتش نشانی" unit group exist
- [ ] At least 1 user with "متصدی شیفت آتش نشانی" position exists

## Functional Testing

### Section 1: General Information

#### Test 1.1: Shift Selection
- [ ] Shift dropdown is visible
- [ ] All shifts are listed (روز/شب/شب۱/شب۲)
- [ ] Can select a shift
- [ ] Selected value persists

#### Test 1.2: Shift Operator (Select2)
- [ ] Dropdown shows search icon
- [ ] Can type to search
- [ ] Results show "Name (Personnel Code)" format
- [ ] Can select an operator
- [ ] Selection displays correctly
- [ ] Dropdown has RTL direction

#### Test 1.3: Firefighter (Select2)
- [ ] Dropdown is searchable
- [ ] Shows all active firefighters
- [ ] Can search by name or code
- [ ] Selection works properly

### Section 2: Incident Summary

#### Test 2.1: Incident Counts
- [ ] All 4 number inputs are visible
- [ ] Default value is 0
- [ ] Can enter numbers
- [ ] Cannot enter negative numbers
- [ ] Cannot enter text

#### Test 2.2: Additional Notes
- [ ] Textarea is visible
- [ ] Can type Persian text
- [ ] Text wraps properly
- [ ] Placeholder shows: "توضیحات تکمیلی..."

### Section 3: Vehicle Status Reports

#### Test 3.1: Initial State
- [ ] One vehicle card appears by default
- [ ] Card has number badge (۱)
- [ ] Vehicle source defaults to "company"
- [ ] Remove button is hidden (minimum 1 vehicle)

#### Test 3.2: Vehicle Source Toggle
- [ ] Two radio buttons are visible
- [ ] "خودروی شرکتی" is pre-selected
- [ ] Click "خودروی پیمانکار" switches view
- [ ] Only one dropdown shows at a time
- [ ] No layout shift when switching
- [ ] Background color changes on selection (indigo)

#### Test 3.3: Company Vehicle Selection
- [ ] Company vehicle dropdown appears when source is "company"
- [ ] Dropdown shows "Model - License Plate" format
- [ ] Can search/select a vehicle
- [ ] Loading spinner appears after selection ⚡
- [ ] Spinner disappears after API response
- [ ] Console shows no errors

#### Test 3.4: Equipment Auto-Disable
**After selecting a company vehicle:**
- [ ] Equipment fields update based on API response
- [ ] Fields with `has_* = false` become disabled
- [ ] Disabled fields show grey background
- [ ] Disabled fields show placeholder: "برای این خودرو تعریف نشده است"
- [ ] Status radio buttons are disabled
- [ ] Enabled fields remain interactive

#### Test 3.5: Contractor Vehicle Selection
- [ ] Switch to "خودروی پیمانکار"
- [ ] Contractor dropdown appears
- [ ] Shows "Contractor Name - License Plate" (if contractor assigned)
- [ ] Can select a vehicle
- [ ] No API call is made (no spinner)
- [ ] All equipment fields remain enabled

#### Test 3.6: Equipment Status Fields
**For each of the 10 equipment types:**
- [ ] Label is visible with icon
- [ ] Two radio buttons: مناسب / نامناسب
- [ ] "مناسب" is pre-selected
- [ ] Can switch to "نامناسب"
- [ ] Textarea for description is present
- [ ] Can type Persian text in description

#### Test 3.7: Add Vehicle
- [ ] Click "افزودن خودروی جدید" button
- [ ] New card animates into view smoothly
- [ ] New card has correct number (۲)
- [ ] Remove button appears on both cards
- [ ] New card has empty/default values
- [ ] Select2 initializes on new dropdowns
- [ ] Can add multiple vehicles (test 3-4)

#### Test 3.8: Remove Vehicle
- [ ] Click trash icon on a vehicle card
- [ ] Card fades out with animation
- [ ] Card disappears completely
- [ ] Remaining cards keep their data
- [ ] Cannot remove when only 1 vehicle remains
- [ ] Numbers re-index properly

### Form Submission

#### Test 4.1: Validation - Empty Required Fields
- [ ] Click "ثبت نهایی گزارش" without filling
- [ ] Form shows validation errors
- [ ] Error messages are in Persian
- [ ] Required fields are highlighted

#### Test 4.2: Validation - Valid Data
- [ ] Fill all required fields
- [ ] Fill at least 1 complete vehicle
- [ ] Click submit
- [ ] Form submits successfully
- [ ] Redirects to detail page
- [ ] Success message appears
- [ ] Data is saved in database

#### Test 4.3: Multiple Vehicles
- [ ] Add 3 vehicles
- [ ] Fill data for all 3
- [ ] Submit form
- [ ] All 3 vehicles are saved
- [ ] Can view all 3 in detail page

#### Test 4.4: Mixed Vehicle Types
- [ ] Add vehicle #1: Company vehicle
- [ ] Add vehicle #2: Contractor vehicle
- [ ] Add vehicle #3: Company vehicle (different)
- [ ] Submit form
- [ ] All vehicles saved correctly
- [ ] Equipment status matches selections

## UI/UX Testing

### Visual Design

#### Test 5.1: Layout & Spacing
- [ ] Main card has rounded corners
- [ ] Sections have clear visual separation
- [ ] Spacing is consistent throughout
- [ ] No overlapping elements
- [ ] Section numbers (۱, ۲, ۳) are visible

#### Test 5.2: Typography
- [ ] Headings are bold and larger
- [ ] Labels are readable
- [ ] Font sizes are appropriate
- [ ] Text color has good contrast

#### Test 5.3: Colors
- [ ] Primary color (indigo) is used consistently
- [ ] Required field asterisks are red
- [ ] Remove button is red-themed
- [ ] Success button is green
- [ ] Hover states work properly

#### Test 5.4: Dark Mode
- [ ] Switch system to dark mode
- [ ] Page adapts automatically
- [ ] All text is readable
- [ ] Borders and shadows are visible
- [ ] No contrast issues
- [ ] Dark mode looks polished

### Responsive Design

#### Test 6.1: Desktop (1920x1080)
- [ ] Layout uses full width (max-w-7xl)
- [ ] 3-column grid for incidents
- [ ] 3-column grid for equipment
- [ ] All elements are well-spaced

#### Test 6.2: Tablet (768x1024)
- [ ] Layout adapts to 2 columns
- [ ] Cards remain readable
- [ ] Buttons are touch-friendly
- [ ] No horizontal scroll

#### Test 6.3: Mobile (375x667)
- [ ] Single column layout
- [ ] Cards stack vertically
- [ ] Buttons are large enough
- [ ] Text is readable
- [ ] Dropdowns work on touch
- [ ] No zoom required

### Interactions

#### Test 7.1: Focus States
- [ ] Tab through form
- [ ] Focus ring appears on each field
- [ ] Focus ring is indigo/blue
- [ ] Focus is visible in dark mode
- [ ] Tab order is logical

#### Test 7.2: Hover States
- [ ] Buttons show hover effect
- [ ] Cards highlight on hover
- [ ] Cursor changes to pointer
- [ ] Transitions are smooth

#### Test 7.3: Transitions & Animations
- [ ] Vehicle cards fade in/out smoothly
- [ ] Loading spinner rotates
- [ ] No janky animations
- [ ] 60fps performance

### RTL & Localization

#### Test 8.1: RTL Layout
- [ ] Text flows right-to-left
- [ ] Icons are on correct side
- [ ] Dropdowns align right
- [ ] Numbers display properly
- [ ] Back arrow points right

#### Test 8.2: Persian Text
- [ ] All labels are in Persian
- [ ] Placeholders are in Persian
- [ ] Error messages are in Persian
- [ ] Button text is Persian
- [ ] No English text visible

## Performance Testing

### Load Time
- [ ] Page loads in < 2 seconds
- [ ] No flash of unstyled content
- [ ] Alpine.js initializes quickly
- [ ] Select2 loads without delay

### API Response
- [ ] Equipment API responds in < 500ms
- [ ] No race conditions
- [ ] Multiple API calls don't conflict
- [ ] Error handling works

### Browser Performance
- [ ] CPU usage is low
- [ ] Memory usage is reasonable
- [ ] No memory leaks (add/remove vehicles 20x)
- [ ] Smooth scrolling

## Browser Compatibility

### Chrome (Latest)
- [ ] All features work
- [ ] Styling is correct
- [ ] No console errors

### Firefox (Latest)
- [ ] All features work
- [ ] Styling is correct
- [ ] No console errors

### Safari (Latest)
- [ ] All features work
- [ ] Styling is correct
- [ ] No console errors

### Edge (Latest)
- [ ] All features work
- [ ] Styling is correct
- [ ] No console errors

## Accessibility Testing

### Keyboard Navigation
- [ ] Can complete form with keyboard only
- [ ] Tab order is logical
- [ ] Enter/Return submits form
- [ ] Escape closes dropdowns

### Screen Reader
- [ ] Form labels are announced
- [ ] Required fields are indicated
- [ ] Error messages are announced
- [ ] Buttons have clear labels

### Color Contrast
- [ ] Text passes WCAG AA (4.5:1)
- [ ] Focus indicators are visible
- [ ] Error colors are distinct

## Security Testing

### CSRF Protection
- [ ] CSRF token is present
- [ ] Form won't submit without token
- [ ] Token refreshes properly

### Input Validation
- [ ] SQL injection is prevented
- [ ] XSS is prevented
- [ ] HTML in textarea is escaped

### Permissions
- [ ] Unauthorized users can't access
- [ ] Proper 403 error shows
- [ ] URL manipulation doesn't bypass checks

## Edge Cases

### Test 10.1: Rapid Clicking
- [ ] Click "Add Vehicle" 10x rapidly
- [ ] All vehicles are added
- [ ] No duplicates
- [ ] No errors

### Test 10.2: Network Issues
- [ ] Disconnect network
- [ ] Select company vehicle
- [ ] API call fails gracefully
- [ ] Error message appears (console)
- [ ] Form remains usable

### Test 10.3: Slow API
- [ ] Throttle network to 3G
- [ ] Select company vehicle
- [ ] Loading spinner shows
- [ ] Response eventually loads
- [ ] UI doesn't break

### Test 10.4: Large Form
- [ ] Add 20 vehicles
- [ ] Fill all fields
- [ ] Submit form
- [ ] All data saves correctly
- [ ] No performance issues

### Test 10.5: Special Characters
- [ ] Type special Persian characters (ژ، چ، پ)
- [ ] Try emoji in descriptions
- [ ] Enter long text (1000 chars)
- [ ] Form handles gracefully

## Regression Testing

### Test 11.1: Edit Existing Report
- [ ] Create a report
- [ ] Navigate to edit page
- [ ] Existing data loads correctly
- [ ] Vehicle cards show saved data
- [ ] Equipment status matches database
- [ ] Can modify and save changes

### Test 11.2: Delete Vehicle in Edit
- [ ] Edit existing report with 2+ vehicles
- [ ] Remove one vehicle
- [ ] Submit form
- [ ] Removed vehicle is deleted from DB
- [ ] Other vehicles remain unchanged

## Final Verification

### Database Integrity
- [ ] Check `fire_reports_firereport` table
- [ ] Check `fire_reports_vehiclestatusreport` table
- [ ] All fields are populated correctly
- [ ] No orphaned records
- [ ] Foreign keys are correct

### Console Logs
- [ ] No JavaScript errors
- [ ] No 404s for resources
- [ ] No CORS errors
- [ ] API calls succeed (200 status)

### User Experience
- [ ] Form feels professional
- [ ] No confusion about what to do
- [ ] Feedback is clear and immediate
- [ ] Process is smooth end-to-end

---

## Sign-Off

**Tester Name**: _________________  
**Date**: _________________  
**All Tests Passed**: ⬜ Yes ⬜ No  
**Issues Found**: _________________  
**Notes**: _________________

---

## Priority Issues Template

If issues are found, use this format:

**Issue #**: _____  
**Severity**: ⬜ Critical ⬜ High ⬜ Medium ⬜ Low  
**Component**: _________________  
**Description**: _________________  
**Steps to Reproduce**:
1. _________________
2. _________________
3. _________________

**Expected**: _________________  
**Actual**: _________________  
**Browser/OS**: _________________  
**Screenshot**: (attach)

---

**Total Tests**: 150+  
**Estimated Testing Time**: 2-3 hours  
**Recommended**: Test in multiple browsers and devices
