#!/usr/bin/env python
"""
اسکریپت برای بررسی فیش‌های حقوقی در دیتابیس
"""
import os
import django

# تنظیم Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.production')
django.setup()

from accounts.models import Payslip, UserProfile
from django.contrib.auth.models import User

def check_payslips():
    """بررسی فیش‌های حقوقی"""
    print("=" * 60)
    print("بررسی فیش‌های حقوقی")
    print("=" * 60)
    
    # تعداد کل فیش‌ها
    total_payslips = Payslip.objects.count()
    print(f"\nتعداد کل فیش‌های حقوقی در دیتابیس: {total_payslips}")
    
    if total_payslips == 0:
        print("⚠️  هیچ فیش حقوقی در دیتابیس وجود ندارد!")
        return
    
    # لیست همه فیش‌ها
    print("\nفهرست فیش‌های حقوقی:")
    print("-" * 60)
    for payslip in Payslip.objects.select_related('user_profile', 'user_profile__user').all():
        print(f"ID: {payslip.id}")
        print(f"  کاربر: {payslip.user_profile.user.get_full_name()} ({payslip.user_profile.user.username})")
        print(f"  کد پرسنلی: {payslip.user_profile.personnel_code}")
        print(f"  سال/ماه: {payslip.year}/{payslip.month:02d}")
        print(f"  فایل: {payslip.file.name if payslip.file else 'None'}")
        print(f"  تاریخ بارگذاری: {payslip.uploaded_at}")
        print()
    
    # بررسی فیش‌های یک کاربر خاص
    print("\n" + "=" * 60)
    print("بررسی فیش‌های کاربر خاص")
    print("=" * 60)
    
    # جستجوی کاربر با کد پرسنلی
    personnel_code = input("\nکد پرسنلی کاربر را وارد کنید (یا Enter برای خروج): ").strip()
    if not personnel_code:
        return
    
    try:
        user_profile = UserProfile.objects.get(personnel_code=personnel_code)
        print(f"\nکاربر یافت شد: {user_profile.user.get_full_name()} ({user_profile.user.username})")
        
        user_payslips = Payslip.objects.filter(user_profile=user_profile)
        print(f"تعداد فیش‌های این کاربر: {user_payslips.count()}")
        
        if user_payslips.exists():
            print("\nفهرست فیش‌های این کاربر:")
            for payslip in user_payslips:
                print(f"  - {payslip.year}/{payslip.month:02d} (ID: {payslip.id})")
        else:
            print("⚠️  هیچ فیشی برای این کاربر یافت نشد!")
            
            # بررسی اینکه آیا فیش‌هایی با کد پرسنلی دیگر وجود دارد
            print("\nبررسی فیش‌های سایر کاربران:")
            other_payslips = Payslip.objects.exclude(user_profile=user_profile)
            if other_payslips.exists():
                print(f"⚠️  {other_payslips.count()} فیش برای کاربران دیگر وجود دارد:")
                for payslip in other_payslips[:5]:  # فقط 5 تا اول
                    print(f"  - کاربر: {payslip.user_profile.user.get_full_name()} "
                          f"({payslip.user_profile.personnel_code}) - "
                          f"{payslip.year}/{payslip.month:02d}")
    except UserProfile.DoesNotExist:
        print(f"⚠️  کاربری با کد پرسنلی '{personnel_code}' یافت نشد!")
        
        # لیست کدهای پرسنلی موجود
        existing_codes = UserProfile.objects.exclude(personnel_code='').values_list('personnel_code', flat=True)
        if existing_codes:
            print(f"\nکدهای پرسنلی موجود ({len(existing_codes)} مورد):")
            for code in existing_codes[:10]:  # فقط 10 تا اول
                print(f"  - {code}")

if __name__ == '__main__':
    check_payslips()

