#!/usr/bin/env python
"""تست تبدیل اعداد فارسی به انگلیسی"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.development')
django.setup()

from accounts.models import UserProfile

# نمونه‌های فایل با اعداد فارسی
test_files = [
    '۱۱۰۰۰۲.pdf',
    '۱۱۰۰۰۳.pdf',
    '۱۱۰۰۴۵.pdf',
    '۱۱۰۰۵۷.pdf',
    '۱۱۰۰۵۸.pdf',
]

print("=" * 70)
print("تست تبدیل اعداد فارسی به انگلیسی")
print("=" * 70)

# تبدیل اعداد فارسی به انگلیسی
persian_digits = '۰۱۲۳۴۵۶۷۸۹'
english_digits = '0123456789'
trans_table = str.maketrans(persian_digits, english_digits)

for filename in test_files:
    base_name = os.path.splitext(filename)[0]
    
    # تبدیل فارسی به انگلیسی
    base_name_english = base_name.translate(trans_table)
    personnel_code = base_name_english.strip()
    
    print(f"\n{filename:<20}")
    print(f"  فارسی:   {base_name}")
    print(f"  انگلیسی: {base_name_english}")
    
    # جستجو در دیتابیس
    try:
        profile = UserProfile.objects.get(personnel_code=personnel_code)
        print(f"  ✓ یافت شد: {profile.user.get_full_name()}")
    except UserProfile.DoesNotExist:
        print(f"  ✗ یافت نشد")
    except UserProfile.MultipleObjectsReturned:
        count = UserProfile.objects.filter(personnel_code=personnel_code).count()
        print(f"  ⚠ چند مورد یافت شد ({count} مورد)")

print("\n" + "=" * 70)
