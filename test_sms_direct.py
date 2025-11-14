#!/usr/bin/env python
"""
اسکریپت تست مستقیم ارسال SMS
برای اجرا: python test_sms_direct.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.production')
django.setup()

from rubika_bot.sms_utils import send_connection_code_sms
from rubika_bot.models import RubikaConnectionCode
from accounts.models import UserProfile
from django.conf import settings

print("=" * 60)
print("تست ارسال SMS کد اتصال روبیکا")
print("=" * 60)

# بررسی تنظیمات
print(f"\n📋 تنظیمات:")
print(f"   SMSIR_API_KEY: {settings.SMSIR_API_KEY[:20]}..." if hasattr(settings, 'SMSIR_API_KEY') and settings.SMSIR_API_KEY else "   ❌ SMSIR_API_KEY تنظیم نشده")
print(f"   SMSIR_LINE_NUMBER: {settings.SMSIR_LINE_NUMBER}" if hasattr(settings, 'SMSIR_LINE_NUMBER') else "   ❌ SMSIR_LINE_NUMBER تنظیم نشده")

# پیدا کردن کاربر
profile = UserProfile.objects.filter(personnel_code='111264').first()
if not profile:
    print("\n❌ کاربر یافت نشد!")
    exit(1)

print(f"\n👤 کاربر:")
print(f"   نام: {profile.user.get_full_name()}")
print(f"   موبایل: {profile.mobile}")

# تولید کد جدید
print(f"\n🔑 تولید کد اتصال...")
RubikaConnectionCode.objects.filter(user=profile.user, used=False).delete()
code = RubikaConnectionCode.generate_for_user(profile.user)
print(f"   کد: {code.code}")
print(f"   طول: {len(code.code)} کاراکتر")

# ارسال SMS
print(f"\n📤 ارسال SMS...")
result = send_connection_code_sms(profile.mobile, code.code)

print(f"\n{'✅' if result else '❌'} نتیجه: {'موفق' if result else 'ناموفق'}")
print("=" * 60)
