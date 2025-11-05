# Visual Design Preview - Fire Report Form 🎨

## Overall Appearance

### Color Palette
```
Primary Colors:
- Indigo: #4F46E5 (indigo-600) - Buttons, focus rings, accents
- Indigo Light: #E0E7FF (indigo-100) - Section badges, equipment icons

Status Colors:
- Green: #16A34A (green-600) - Submit button, success states
- Red: #DC2626 (red-600) - Remove button, error states
- Gray: #F9FAFB to #111827 (gray-50 to gray-900) - Backgrounds, text

Semantic Colors:
- Success: Green tones
- Warning: Amber tones
- Error: Red tones
- Info: Indigo tones
```

### Typography Scale
```
Headings:
- H1 (Page Title): 3xl (1.875rem) - Bold
- H2 (Section Title): xl (1.25rem) - Bold
- H3 (Card Title): lg (1.125rem) - Bold
- H4 (Subsection): base (1rem) - Bold

Body Text:
- Labels: sm (0.875rem) - Semibold
- Input Text: base (1rem) - Regular
- Helper Text: xs (0.75rem) - Regular
- Placeholders: sm (0.875rem) - Regular
```

### Spacing System
```
Padding:
- Main Card: 8 (2rem)
- Vehicle Cards: 6 (1.5rem)
- Form Controls: py-2.5 px-3

Margins:
- Between Sections: 10 (2.5rem)
- Between Fields: 6 (1.5rem)
- Between Cards: 6 (1.5rem)

Gaps:
- Grid Columns: 6 (1.5rem)
- Icon + Text: 2-3 (0.5rem-0.75rem)
```

## Section-by-Section Visual Guide

### Page Header
```
┌─────────────────────────────────────────────────────────┐
│  [←]  ثبت گزارش آتش‌نشانی                               │
│       لطفاً تمام بخش‌های فرم را با دقت تکمیل نمایید      │
└─────────────────────────────────────────────────────────┘

Elements:
- Back button: White rounded square with arrow
- Title: Large, bold, dark gray
- Subtitle: Smaller, lighter gray
```

### Main Card Container
```
┌───────────────────────────────────────────────────────────┐
│ ╔═══════════════════════════════════════════════════════╗ │
│ ║                     MAIN CARD                         ║ │
│ ║  • White background (light mode)                      ║ │
│ ║  • Dark gray background (dark mode)                   ║ │
│ ║  • Rounded corners (xl)                              ║ │
│ ║  • Soft shadow (shadow-lg)                           ║ │
│ ║  • Subtle border                                     ║ │
│ ╚═══════════════════════════════════════════════════════╝ │
└───────────────────────────────────────────────────────────┘
```

### Section 1: General Information
```
┌─────────────────────────────────────────────────────────┐
│  [۱] اطلاعات کلی                                         │
│  ─────────────────────────────────────────────────────   │
│                                                          │
│  شیفت *             اپراتور شیفت *        آتش‌نشان *     │
│  [Dropdown ▼]      [Search... 🔍]        [Search... 🔍]  │
│                                                          │
└─────────────────────────────────────────────────────────┘

Visual Details:
- Number badge: Indigo background, white text, rounded
- Divider: Light gray horizontal line
- 3-column responsive grid
- Select2 dropdowns: Search icon, placeholder text
- Required asterisks: Red color
```

### Section 2: Incident Summary
```
┌─────────────────────────────────────────────────────────┐
│  [۲] خلاصه حوادث                                         │
│  ─────────────────────────────────────────────────────   │
│                                                          │
│  تعداد اعزام    تعداد پرسنلی    تعداد تجهیزاتی    آتش  │
│    [  0  ]        [  0  ]         [  0  ]        [  0 ] │
│                                                          │
│  توضیحات تکمیلی                                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │ توضیحات تکمیلی...                                   ││
│  │                                                     ││
│  │                                                     ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘

Visual Details:
- 4-column grid for numbers
- Number inputs: Centered text, rounded borders
- Textarea: Large, resizable, rounded corners
- Light border with focus ring effect
```

### Section 3: Vehicle Status Reports
```
┌─────────────────────────────────────────────────────────┐
│  [۳] گزارش وضعیت خودروها                                 │
│  ─────────────────────────────────────────────────────   │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │ ╔═══════════════════════════════════════════════╗ │  │
│  │ ║ [۱] خودرو شماره ۱             [⌛] [🗑️]      ║ │  │
│  │ ╚═══════════════════════════════════════════════╝ │  │
│  │                                                   │  │
│  │  منبع خودرو *                                    │  │
│  │  ┌──────────────────┬──────────────────┐        │  │
│  │  │ 🏢 خودروی شرکتی │ 🤝 خودروی پیمانکار│        │  │
│  │  └──────────────────┴──────────────────┘        │  │
│  │  (Segmented control - indigo when active)       │  │
│  │                                                   │  │
│  │  انتخاب خودرو *                                  │  │
│  │  [Select vehicle... ▼]                          │  │
│  │                                                   │  │
│  │  وضعیت تجهیزات و خودرو                          │  │
│  │  ────────────────────────────────────            │  │
│  │                                                   │  │
│  │  ┌─────────────────────────────────────────────┐│  │
│  │  │ [🚨] بوق و چراغ   ◉ مناسب ○ نامناسب        ││  │
│  │  │ [Text area...]                               ││  │
│  │  └─────────────────────────────────────────────┘│  │
│  │  (Repeats for all 10 equipment types)           │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  [+ افزودن خودروی جدید]                                 │
│                                                          │
└─────────────────────────────────────────────────────────┘

Vehicle Card Details:
- Light gray background (slate-50)
- Darker in dark mode
- Rounded corners
- Number badge: Indigo circle
- Loading spinner: Animated, indigo color
- Remove button: Red, rounded, trash icon
- Equipment rows: Bordered, hover effect
```

### Equipment Row (Detailed)
```
┌─────────────────────────────────────────────────────────┐
│  [Icon] Equipment Name     ◉ مناسب ○ نامناسب           │
│  ───────────────────────                                │
│  [Multiline text area for description...]              │
└─────────────────────────────────────────────────────────┘

When Disabled:
┌─────────────────────────────────────────────────────────┐
│  [Icon] Equipment Name     ⊗ مناسب ⊗ نامناسب  (grayed) │
│  ───────────────────────────                            │
│  [برای این خودرو تعریف نشده است]  (grayed, disabled)   │
└─────────────────────────────────────────────────────────┘
```

### Form Actions
```
┌─────────────────────────────────────────────────────────┐
│                            ────────────────────────────  │
│                            [انصراف] [✓ ثبت نهایی گزارش] │
└─────────────────────────────────────────────────────────┘

Button Styles:
- Cancel: Gray background, rounded, hover effect
- Submit: Green background, white text, shadow, icon
- Border top: Light gray separator
```

## Interactive States

### Hover States
```
Buttons:
- Background darkens slightly
- Shadow increases
- Smooth 200ms transition

Cards:
- Border color changes (to indigo)
- Subtle shadow increase

Form Controls:
- Border color brightens
- Cursor changes to pointer
```

### Focus States
```
All Input Elements:
- 2px indigo ring appears
- Border changes to indigo
- Ring offset for better visibility
- Smooth transition

Visual Example:
┌─────────────────────────────┐
│ [Your text here]            │ ← Normal
└─────────────────────────────┘

╔═════════════════════════════╗
║ [Your text here]            ║ ← Focused (with ring)
╚═════════════════════════════╝
```

### Loading States
```
During API Call:
┌─────────────────────────────────────────┐
│ [۱] خودرو شماره ۱  [⌛ در حال بارگذاری...] │
└─────────────────────────────────────────┘

Spinner:
  ⟳  ← Rotating animation (360° continuous)
```

### Disabled States
```
Equipment Field (Not Available):
┌─────────────────────────────────────────┐
│ [Icon] Equipment Name  (50% opacity)    │
│ ⊗ مناسب ⊗ نامناسب (grayed)              │
│ [برای این خودرو تعریف نشده است]          │
│ (cursor: not-allowed)                   │
└─────────────────────────────────────────┘
```

## Animations & Transitions

### Adding Vehicle
```
Frame 1: Button Click
        [+ افزودن خودروی جدید]  ← Click

Frame 2: New Card Appears (opacity: 0, scale: 0.95)
        [Invisible card]

Frame 3: Animation Progress (opacity: 0.5, scale: 0.975)
        [Semi-visible card]

Frame 4: Complete (opacity: 1, scale: 1)
        [Fully visible card]

Duration: 300ms, ease-out
```

### Removing Vehicle
```
Frame 1: Trash Icon Click
        [🗑️]  ← Click

Frame 2: Fade Begins (opacity: 1 → 0.5)
        [Card dimming]

Frame 3: Scale Down (scale: 1 → 0.95)
        [Card shrinking]

Frame 4: Gone (opacity: 0, display: none)
        [Card removed]

Duration: 200ms, ease-in
```

### Source Toggle Animation
```
Before: [Company Selected] [Contractor]
        ↓
After:  [Company] [Contractor Selected]

- Background color crossfades (200ms)
- Text color crossfades (200ms)
- Shadow appears/disappears (200ms)
- Dropdown swaps instantly (no layout shift)
```

## Responsive Breakpoints

### Desktop (1024px+)
```
┌─────────────────────────────────────────────────────────┐
│  Page Header                                             │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Section 1: [Field] [Field] [Field]                  ││
│  │ Section 2: [Num] [Num] [Num] [Num]                 ││
│  │            [Textarea...........................]     ││
│  │ Section 3: [Vehicle Card - 3 cols equipment]        ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### Tablet (768px-1023px)
```
┌────────────────────────────────────────┐
│  Page Header                            │
│  ┌────────────────────────────────────┐│
│  │ Section 1: [Field] [Field]         ││
│  │            [Field]                  ││
│  │ Section 2: [Num] [Num]             ││
│  │            [Num] [Num]              ││
│  │            [Textarea.............] ││
│  │ Section 3: [Vehicle - 2 cols]      ││
│  └────────────────────────────────────┘│
└────────────────────────────────────────┘
```

### Mobile (< 768px)
```
┌────────────────────┐
│  Header            │
│  ┌────────────────┐│
│  │ Section 1:     ││
│  │ [Field]        ││
│  │ [Field]        ││
│  │ [Field]        ││
│  │                ││
│  │ Section 2:     ││
│  │ [Num]          ││
│  │ [Num]          ││
│  │ [Num]          ││
│  │ [Num]          ││
│  │ [Textarea...]  ││
│  │                ││
│  │ Section 3:     ││
│  │ [Vehicle Card] ││
│  │ (1 col)        ││
│  └────────────────┘│
└────────────────────┘
```

## Dark Mode Transformation

### Light Mode → Dark Mode
```
Component         | Light             | Dark
─────────────────────────────────────────────────
Page Background   | gray-50 (#F9FAFB) | gray-900 (#111827)
Card Background   | white (#FFFFFF)   | gray-800 (#1F2937)
Vehicle Card BG   | slate-50          | gray-800/50
Text Primary      | gray-900          | gray-100
Text Secondary    | gray-700          | gray-300
Borders           | gray-300          | gray-600
Focus Ring        | indigo-500        | indigo-500
Shadows           | Subtle            | More pronounced
```

### Visual Comparison
```
Light Mode:
┌─────────────────────────┐
│ ⬜ White background     │
│ ⬛ Dark text            │
│ ─── Light borders       │
└─────────────────────────┘

Dark Mode:
┌─────────────────────────┐
│ ⬛ Dark background      │
│ ⬜ Light text           │
│ ─── Medium borders      │
└─────────────────────────┘
```

## Accessibility Features

### Visual Indicators
```
Focus Visible:
  ┏━━━━━━━━━━━━━━━┓
  ┃ Focused Input ┃  ← 2px indigo ring
  ┗━━━━━━━━━━━━━━━┛

Error State:
  ┌───────────────┐
  │ Invalid Input │  ← Red border
  └───────────────┘
  ❌ Error message

Success State:
  ┌───────────────┐
  │ Valid Input ✓ │  ← Green border
  └───────────────┘
```

### Icon Legend
```
🏢 - Company/Organization
🤝 - Contractor/Partnership
🚨 - Horn & Siren
💧 - Water/Hoses
📺 - Monitor/Screen
🧯 - Fire Extinguisher
🧰 - Equipment/Toolbox
💨 - Foam/Spray
⭕ - Tires/Wheels
🛑 - Brakes/Stop
💡 - Lighting
⌛ - Loading/Processing
🗑️ - Delete/Remove
✓ - Success/Check
❌ - Error/Cancel
```

## Print Styles (Future Enhancement)
```
When printing:
- Remove shadows
- Convert colors to print-friendly
- Hide interactive elements (buttons)
- Expand all cards
- Add page breaks between vehicles
- Show URLs for links
```

---

## Implementation Notes

### CSS Classes Used
```css
Layout:
- max-w-7xl, mx-auto, px-4, py-6
- grid, grid-cols-1, md:grid-cols-3, gap-6
- space-y-10, space-y-6

Cards:
- bg-white, dark:bg-gray-800
- rounded-xl, shadow-lg
- border, border-gray-200, dark:border-gray-700
- p-8, p-6

Typography:
- text-3xl, text-xl, text-lg, text-base, text-sm, text-xs
- font-bold, font-semibold
- text-gray-900, dark:text-gray-100

Colors:
- bg-indigo-600, text-indigo-600
- bg-green-600, bg-red-600
- hover:bg-indigo-700

States:
- focus:ring-2, focus:ring-indigo-500
- hover:bg-gray-50, dark:hover:bg-gray-700
- disabled:opacity-40, disabled:cursor-not-allowed

Animations:
- transition-colors, transition-all
- duration-200, duration-300
- ease-in, ease-out
```

---

**Design System**: Tailwind CSS v3.x
**Component Library**: Alpine.js v3.x
**Design Inspiration**: Stripe, Linear, Notion
**Language**: Persian (Farsi) - RTL
**Accessibility**: WCAG 2.1 AA Compliant
