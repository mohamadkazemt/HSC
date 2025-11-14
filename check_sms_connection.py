#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
اسکریپت بررسی مشکل اتصال از طریق SMS
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.base')
django.setup()

from accounts.models import UserProfile

print("=" * 70)
print("بررسی پروفایل‌های کاربری")
print("=" * 70)

# کد پرسنلی که کاربر وارد کرده
personnel_code_input = "111264"
national_code_input = "3080002131"

print(f"\n🔍 جستجو برای:")
print(f"   کد ملی: {national_code_input}")
print(f"   کد پرسنلی: {personnel_code_input}")
print()

# جستجوی دقیق
profile = UserProfile.objects.filter(
    national_code=national_code_input,
    personnel_code=personnel_code_input
).select_related('user').first()

if profile:
    print("✅ پروفایل یافت شد:")
    print(f"   نام: {profile.user.get_full_name()}")
    print(f"   نام کاربری: {profile.user.username}")
    print(f"   کد ملی: {profile.national_code}")
    print(f"   کد پرسنلی: {profile.personnel_code}")
    print(f"   موبایل: {profile.mobile}")
else:
    print("❌ پروفایلی با این مشخصات یافت نشد!")
    print()
    
    # بررسی با کد پرسنلی فقط
    print("🔍 جستجو فقط با کد پرسنلی...")
    profiles_by_personnel = UserProfile.objects.filter(
        personnel_code=personnel_code_input
    ).select_related('user')
    
    if profiles_by_personnel.exists():
        print(f"✅ {profiles_by_personnel.count()} پروفایل با این کد پرسنلی:")
        for p in profiles_by_personnel:
            print(f"   - نام: {p.user.get_full_name()}")
            print(f"     کد ملی: {p.national_code or 'خالی'}")
            print(f"     کد پرسنلی: {p.personnel_code}")
            print(f"     موبایل: {p.mobile or 'خالی'}")
            print()
    else:
        print("❌ هیچ پروفایلی با این کد پرسنلی وجود ندارد")
    
    # بررسی با کد ملی فقط
    print("🔍 جستجو فقط با کد ملی...")
    profiles_by_national = UserProfile.objects.filter(
        national_code=national_code_input
    ).select_related('user')
    
    if profiles_by_national.exists():
        print(f"✅ {profiles_by_national.count()} پروفایل با این کد ملی:")
        for p in profiles_by_national:
            print(f"   - نام: {p.user.get_full_name()}")
            print(f"     کد ملی: {p.national_code}")
            print(f"     کد پرسنلی: {p.personnel_code or 'خالی'}")
            print(f"     موبایل: {p.mobile or 'خالی'}")
            print()
    else:
        print("❌ هیچ پروفایلی با این کد ملی وجود ندارد")

print()
print("=" * 70)
print("بررسی تمام پروفایل‌های دارای کد ملی")
print("=" * 70)

all_with_national = UserProfile.objects.exclude(
    national_code__isnull=True
).exclude(
    national_code=''
).select_related('user')

print(f"\n📊 تعداد کل پروفایل‌های دارای کد ملی: {all_with_national.count()}")

if all_with_national.exists():
    print("\n📋 لیست پروفایل‌ها:")
    for p in all_with_national[:10]:  # فقط 10 تای اول
        print(f"   - {p.user.get_full_name()}")
        print(f"     کد ملی: {p.national_code}")
        print(f"     کد پرسنلی: {p.personnel_code or 'خالی'}")
        print(f"     موبایل: {p.mobile or 'خالی'}")
        print()

print("=" * 70)
