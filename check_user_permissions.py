#!/usr/bin/env python
"""
اسکریپت بررسی دسترسی‌های کاربر mkt
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.development')
django.setup()

from django.contrib.auth.models import User
from permissions.models import UserPermission, SectionPermission, PositionPermission, PartPermission
from permissions.utils import check_permission

# پیدا کردن کاربر mkt
try:
    user = User.objects.get(username='mkt')
    print(f"✓ کاربر پیدا شد: {user.username} (ID: {user.id})")
    print(f"  - نام: {user.get_full_name()}")
    print(f"  - ایمیل: {user.email}")
    print(f"  - سوپریوزر: {user.is_superuser}")
    print(f"  - استاف: {user.is_staff}")
    print()
    
    # بررسی پروفایل
    if hasattr(user, 'userprofile'):
        profile = user.userprofile
        print("✓ پروفایل کاربر:")
        print(f"  - بخش (Section): {profile.section}")
        print(f"  - قسمت (Part): {profile.part}")
        print(f"  - سمت (Position): {profile.position}")
        print(f"  - گروه واحد (Unit Group): {profile.unit_group}")
        print()
    else:
        print("✗ پروفایل کاربر وجود ندارد!")
        print()
    
    # بررسی دسترسی‌های مستقیم کاربر
    user_perms = UserPermission.objects.filter(user=user)
    print(f"دسترسی‌های مستقیم کاربر: {user_perms.count()} مورد")
    for perm in user_perms:
        print(f"  - {perm.view_name}: {perm}")
    print()
    
    # بررسی دسترسی‌های بخش
    if hasattr(user, 'userprofile') and user.userprofile.section:
        section_perms = SectionPermission.objects.filter(section=user.userprofile.section)
        print(f"دسترسی‌های بخش ({user.userprofile.section}): {section_perms.count()} مورد")
        for perm in section_perms:
            print(f"  - {perm.view_name}")
    print()
    
    # بررسی دسترسی‌های سمت
    if hasattr(user, 'userprofile') and user.userprofile.position:
        position_perms = PositionPermission.objects.filter(position=user.userprofile.position)
        print(f"دسترسی‌های سمت ({user.userprofile.position}): {position_perms.count()} مورد")
        for perm in position_perms:
            print(f"  - {perm.view_name}")
    print()
    
    # بررسی دسترسی‌های قسمت
    if hasattr(user, 'userprofile') and user.userprofile.part:
        part_perms = PartPermission.objects.filter(part=user.userprofile.part)
        print(f"دسترسی‌های قسمت ({user.userprofile.part}): {part_perms.count()} مورد")
        for perm in part_perms:
            print(f"  - {perm.view_name}")
    print()
    
    # تست دسترسی‌های خاص برای leave_reports
    print("="*60)
    print("تست دسترسی‌های مرخصی:")
    print("="*60)
    
    views_to_check = [
        'request_leave',
        'my_inbox',
        'leave_archive',
    ]
    
    for view_name in views_to_check:
        result = check_permission(user, view_name)
        if result:
            print(f"✓ {view_name}: {result}")
        else:
            print(f"✗ {view_name}: دسترسی وجود ندارد!")
    
except User.DoesNotExist:
    print("✗ کاربر با نام کاربری 'mkt' پیدا نشد!")
