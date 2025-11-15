#!/usr/bin/env python
"""
اسکریپت بررسی کدهای پرسنلی برای فایل‌های فیش حقوقی
این اسکریپت کمک می‌کند تا کدهای پرسنلی موجود در نام فایل‌ها را با دیتابیس مقایسه کنید
"""
import os
import sys
import django

# تنظیم Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.production')
django.setup()

from accounts.models import UserProfile
from django.contrib.auth.models import User

def extract_personnel_code(filename):
    """استخراج کد پرسنلی از نام فایل"""
    base_name = os.path.splitext(filename)[0]
    
    # اگر فایل به صورت "12345.pdf" باشد
    if base_name.isdigit():
        return base_name
    
    # اگر فایل به صورت "12345_1403_01.pdf" باشد
    parts = base_name.split('_')
    if len(parts) > 0 and parts[0].isdigit():
        return parts[0]
    
    return None

def check_personnel_codes_from_list(file_list):
    """بررسی کدهای پرسنلی از لیست فایل‌ها"""
    print("=" * 80)
    print("بررسی کدهای پرسنلی")
    print("=" * 80)
    
    found = []
    not_found = []
    
    for filename in file_list:
        personnel_code = extract_personnel_code(filename)
        if not personnel_code:
            not_found.append((filename, "نام فایل نامعتبر"))
            continue
        
        try:
            profile = UserProfile.objects.get(personnel_code=personnel_code)
            found.append((filename, personnel_code, profile.user.get_full_name()))
        except UserProfile.DoesNotExist:
            not_found.append((filename, personnel_code))
        except UserProfile.MultipleObjectsReturned:
            profiles = UserProfile.objects.filter(personnel_code=personnel_code)
            found.append((filename, personnel_code, f"چند پروفایل ({profiles.count()})"))
    
    # نمایش نتایج
    print(f"\n✅ فایل‌های یافت شده: {len(found)}")
    print("-" * 80)
    for filename, code, name in found:
        print(f"  ✓ {filename:<30} → کد: {code:<10} → {name}")
    
    print(f"\n❌ فایل‌های یافت نشده: {len(not_found)}")
    print("-" * 80)
    for item in not_found:
        if len(item) == 2:
            filename, code = item
            print(f"  ✗ {filename:<30} → کد: {code:<10} → یافت نشد")
        else:
            filename, reason = item
            print(f"  ✗ {filename:<30} → {reason}")
    
    # پیشنهادات
    if not_found:
        print("\n" + "=" * 80)
        print("💡 پیشنهادات:")
        print("=" * 80)
        
        codes = [item[1] for item in not_found if len(item) == 2]
        if codes:
            print("\nکدهای پرسنلی یافت نشده:")
            for code in sorted(set(codes)):
                print(f"  - {code}")
            
            print("\nاقدامات پیشنهادی:")
            print("  1. بررسی کنید که این کدهای پرسنلی در سیستم ثبت شده‌اند")
            print("  2. از قسمت مدیریت پرسنل، این کدها را اضافه کنید")
            print("  3. یا نام فایل‌ها را با کدهای موجود تطبیق دهید")
            
            # جستجوی کدهای مشابه
            print("\n🔍 جستجوی کدهای مشابه در دیتابیس:")
            for code in sorted(set(codes)):
                # جستجوی کدهای شروع‌شونده با این الگو
                prefix = code[:3] if len(code) >= 3 else code
                similar = UserProfile.objects.filter(
                    personnel_code__startswith=prefix
                ).values_list('personnel_code', 'user__first_name', 'user__last_name')[:5]
                
                if similar:
                    print(f"\n  کدهای مشابه {code}:")
                    for pc, fname, lname in similar:
                        print(f"    - {pc}: {fname} {lname}")
    
    return found, not_found

def check_from_files_input():
    """دریافت نام فایل‌ها از کاربر"""
    print("=" * 80)
    print("لیست نام فایل‌های PDF را وارد کنید (هر کدام در یک خط)")
    print("برای پایان، یک خط خالی وارد کنید")
    print("=" * 80)
    print()
    
    files = []
    while True:
        line = input().strip()
        if not line:
            break
        if line.endswith('.pdf'):
            files.append(line)
    
    if not files:
        print("❌ هیچ فایلی وارد نشد!")
        return
    
    check_personnel_codes_from_list(files)

def check_all_personnel_codes():
    """نمایش تمام کدهای پرسنلی موجود"""
    print("=" * 80)
    print("لیست کدهای پرسنلی موجود در سیستم")
    print("=" * 80)
    
    profiles = UserProfile.objects.select_related('user').order_by('personnel_code')
    
    print(f"\nتعداد کل: {profiles.count()}\n")
    
    for profile in profiles:
        print(f"  {profile.personnel_code:<10} → {profile.user.get_full_name()}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--list':
            check_all_personnel_codes()
        elif sys.argv[1] == '--help':
            print("استفاده:")
            print("  python check_personnel_codes.py          # بررسی از طریق ورودی")
            print("  python check_personnel_codes.py --list   # نمایش تمام کدها")
            print("  python check_personnel_codes.py --help   # نمایش راهنما")
        else:
            # فایل‌ها به عنوان آرگومان
            files = [f for f in sys.argv[1:] if f.endswith('.pdf')]
            if files:
                check_personnel_codes_from_list(files)
    else:
        # حالت تعاملی
        print("\nگزینه‌ها:")
        print("  1. بررسی فایل‌های خاص")
        print("  2. نمایش تمام کدهای پرسنلی")
        print()
        choice = input("انتخاب کنید (1 یا 2): ").strip()
        
        if choice == '1':
            check_from_files_input()
        elif choice == '2':
            check_all_personnel_codes()
        else:
            print("❌ انتخاب نامعتبر!")
