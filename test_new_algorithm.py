#!/usr/bin/env python
"""تست الگوریتم جدید"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.development')
django.setup()

from accounts.models import UserProfile

# شبیه‌سازی فایل‌ها
test_files = [
    '11003.pdf',
    '11004.pdf',
    '11040.pdf',
    '11057.pdf',
    '11058.pdf',
]

print("=" * 70)
print("تست الگوریتم جدید جستجوی کد پرسنلی")
print("=" * 70)

for filename in test_files:
    base_name = os.path.splitext(filename)[0]
    personnel_code = base_name.strip()
    
    # اگر نام فایل شامل _ است، قسمت اول را بگیر
    if '_' in personnel_code:
        personnel_code = personnel_code.split('_')[0].strip()
    
    # اگر کد 5 رقمی است و با 11 شروع می‌شود
    if len(personnel_code) == 5 and personnel_code.startswith('11'):
        personnel_code_6digit = personnel_code[:3] + '0' + personnel_code[3:]  # 11003 -> 110003
    else:
        personnel_code_6digit = None
    
    # جستجو
    user_profile = None
    tried_codes = []
    
    # ابتدا با کد اصلی
    try:
        user_profile = UserProfile.objects.get(personnel_code=personnel_code)
        tried_codes.append(personnel_code)
        status = f"✓ یافت شد با کد {personnel_code}"
    except UserProfile.DoesNotExist:
        tried_codes.append(personnel_code)
        # حالا کد 6 رقمی
        if personnel_code_6digit:
            try:
                user_profile = UserProfile.objects.get(personnel_code=personnel_code_6digit)
                tried_codes.append(personnel_code_6digit)
                status = f"✓ یافت شد با کد {personnel_code_6digit}"
            except UserProfile.DoesNotExist:
                tried_codes.append(personnel_code_6digit)
                status = f"✗ یافت نشد (امتحان شد: {', '.join(tried_codes)})"
            except UserProfile.MultipleObjectsReturned:
                user_profile = UserProfile.objects.filter(personnel_code=personnel_code_6digit).first()
                tried_codes.append(personnel_code_6digit)
                status = f"⚠ چند مورد یافت شد با کد {personnel_code_6digit}"
        else:
            status = f"✗ یافت نشد (امتحان شد: {', '.join(tried_codes)})"
    except UserProfile.MultipleObjectsReturned:
        user_profile = UserProfile.objects.filter(personnel_code=personnel_code).first()
        tried_codes.append(personnel_code)
        status = f"⚠ چند مورد یافت شد با کد {personnel_code}"
    
    print(f"\n{filename:<20} → {status}")
    if user_profile:
        print(f"{'':20}   نام: {user_profile.user.get_full_name()}")
