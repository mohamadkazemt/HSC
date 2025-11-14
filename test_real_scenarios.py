"""
مثال‌های واقعی استفاده از normalize_digits در ربات Rubika
"""

# شبیه‌سازی ورودی‌های مختلف کاربر
print("=" * 70)
print("مثال‌های واقعی استفاده از اعداد فارسی در ربات")
print("=" * 70)
print()

# تابع normalize_digits
def normalize_digits(text: str) -> str:
    if not text:
        return text
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    arabic_digits = '٠١٢٣٤٥٦٧٨٩'
    english_digits = '0123456789'
    translation_table = str.maketrans(
        persian_digits + arabic_digits,
        english_digits + english_digits
    )
    return text.translate(translation_table)


# سناریو 1: اتصال با کد ملی
print("📱 سناریو 1: اتصال با SMS (کد ملی)")
print("-" * 70)
print("👤 کاربر: میخوام با SMS وصل شم")
print("🤖 ربات: لطفاً کد ملی خود را وارد کنید")
print()

user_inputs = [
    "۱۲۳۴۵۶۷۸۹۰",  # کاربر با کیبورد فارسی تایپ می‌کند
    "٠١٢٣٤٥٦٧٨٩",  # کاربر با کیبورد عربی تایپ می‌کند
    "1234567890",    # کاربر با کیبورد انگلیسی تایپ می‌کند
]

for i, input_text in enumerate(user_inputs, 1):
    normalized = normalize_digits(input_text)
    status = "✅ قبول" if normalized.isdigit() and len(normalized) == 10 else "❌ رد"
    print(f"  حالت {i}: ورودی کاربر: {input_text}")
    print(f"          بعد از normalize: {normalized}")
    print(f"          وضعیت: {status}")
    print()

# سناریو 2: درخواست مرخصی (تاریخ)
print("🏖️ سناریو 2: ثبت درخواست مرخصی (تاریخ)")
print("-" * 70)
print("👤 کاربر: میخوام مرخصی بگیرم")
print("🤖 ربات: لطفاً تاریخ مرخصی را وارد کنید (مثال: 1403/09/15)")
print()

date_inputs = [
    "۱۴۰۳/۰۹/۱۵",     # فارسی خالص
    "1403/09/15",      # انگلیسی خالص
    "۱۴۰۳/09/۱۵",     # ترکیبی
    "۱۴۰۳-۰۹-۱۵",     # فارسی با خط تیره
]

for i, input_text in enumerate(date_inputs, 1):
    normalized = normalize_digits(input_text.strip()).replace(' ', '').replace('/', '-')
    print(f"  حالت {i}: ورودی کاربر: {input_text}")
    print(f"          بعد از normalize: {normalized}")
    print(f"          وضعیت: ✅ قبول و پردازش می‌شود")
    print()

# سناریو 3: مرخصی ساعتی (ساعت)
print("⏰ سناریو 3: ثبت مرخصی ساعتی (ساعات)")
print("-" * 70)
print("👤 کاربر: میخوام ساعتی مرخصی بگیرم")
print("🤖 ربات: لطفاً ساعت شروع و پایان را وارد کنید (مثال: 08:00-12:00)")
print()

time_inputs = [
    "۰۸:۰۰-۱۲:۰۰",    # فارسی خالص
    "08:00-12:00",     # انگلیسی خالص
    "۰۸:۰۰ - ۱۲:۰۰",  # فارسی با فاصله
    "14:۳۰-18:00",     # ترکیبی
]

import re
time_pattern = r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})'

for i, input_text in enumerate(time_inputs, 1):
    normalized = normalize_digits(input_text.strip())
    match = re.match(time_pattern, normalized)
    status = "✅ قبول" if match else "❌ رد"
    print(f"  حالت {i}: ورودی کاربر: {input_text}")
    print(f"          بعد از normalize: {normalized}")
    if match:
        start_h, start_m, end_h, end_m = match.groups()
        print(f"          پارس شده: {start_h}:{start_m} تا {end_h}:{end_m}")
    print(f"          وضعیت: {status}")
    print()

# سناریو 4: کد پرسنلی جایگزین
print("👤 سناریو 4: انتخاب جایگزین (کد پرسنلی)")
print("-" * 70)
print("👤 کاربر: میخوام فلانی رو جایگزین انتخاب کنم")
print("🤖 ربات: لطفاً کد پرسنلی جایگزین را وارد کنید")
print()

personnel_inputs = [
    "۱۲۳۴۵",      # فارسی
    "12345",       # انگلیسی
    "١٢٣٤٥",      # عربی
    "۱۲345",       # ترکیبی
]

for i, input_text in enumerate(personnel_inputs, 1):
    normalized = normalize_digits(input_text.strip())
    status = "✅ قبول" if normalized.isdigit() else "❌ رد"
    print(f"  حالت {i}: ورودی کاربر: {input_text}")
    print(f"          بعد از normalize: {normalized}")
    print(f"          وضعیت: {status}")
    print()

# خلاصه
print("=" * 70)
print("📊 خلاصه")
print("=" * 70)
print("✅ همه اعداد فارسی، عربی و انگلیسی قبول می‌شوند")
print("✅ کاربر نیازی به تغییر کیبورد ندارد")
print("✅ تبدیل خودکار و شفاف انجام می‌شود")
print("✅ ترکیبی از اعداد مختلف هم کار می‌کند")
print("=" * 70)
