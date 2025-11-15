#!/usr/bin/env python
"""بررسی کدهای پرسنلی خاص"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.development')
django.setup()

from accounts.models import UserProfile

# کدهای پرسنلی که در فایل‌ها هستند
codes = ['11003', '11004', '11040', '11057', '11058']

print("=" * 60)
print("بررسی کدهای پرسنلی")
print("=" * 60)

for code in codes:
    exists = UserProfile.objects.filter(personnel_code=code).exists()
    if exists:
        profile = UserProfile.objects.get(personnel_code=code)
        print(f"✓ کد {code}: موجود - {profile.user.get_full_name()}")
    else:
        print(f"✗ کد {code}: یافت نشد")
        
        # جستجوی کدهای مشابه
        similar = UserProfile.objects.filter(
            personnel_code__startswith=code[:3]
        ).values_list('personnel_code', flat=True)[:5]
        
        if similar:
            print(f"   کدهای مشابه: {', '.join(similar)}")

print("\n" + "=" * 60)
print("تمام کدهای شروع‌شونده با 110:")
print("=" * 60)

profiles = UserProfile.objects.filter(
    personnel_code__startswith='110'
).select_related('user').order_by('personnel_code')

for profile in profiles:
    print(f"  {profile.personnel_code} → {profile.user.get_full_name()}")

print(f"\nتعداد کل: {profiles.count()}")
