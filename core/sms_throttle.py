"""مدیریت محدودیت نرخ ارسال پیامک (Rate Limiting) برای جلوگیری از سوءاستفاده و هزینه‌های اضافی.

استفاده از Redis برای ذخیره‌سازی شمارش‌های موقت (اگر Redis موجود نباشد، از cache محلی استفاده می‌شود).

تنظیمات پیکربندی در settings.py:
    SMS_RATE_LIMIT_PER_USER_HOUR = 10  # حداکثر تعداد پیامک هر کاربر در ساعت
    SMS_RATE_LIMIT_GLOBAL_MINUTE = 100  # حداکثر تعداد پیامک کل سیستم در دقیقه
    SMS_RATE_LIMIT_ENABLED = True  # فعال/غیرفعال کردن محدودیت

نمونه استفاده:
    from core.sms_throttle import check_sms_rate_limit
    
    ok, reason = check_sms_rate_limit(user_id=123, mobile="09123456789")
    if not ok:
        logger.warning(f"Rate limit exceeded: {reason}")
        return False
    
    # ادامه ارسال پیامک
"""

import logging
from typing import Tuple, Optional
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

SMS_RATE_LIMIT_ENABLED = getattr(settings, 'SMS_RATE_LIMIT_ENABLED', True)
SMS_RATE_LIMIT_PER_USER_HOUR = getattr(settings, 'SMS_RATE_LIMIT_PER_USER_HOUR', 10)
SMS_RATE_LIMIT_GLOBAL_MINUTE = getattr(settings, 'SMS_RATE_LIMIT_GLOBAL_MINUTE', 100)


def _get_user_key(user_id: int) -> str:
    return f"sms_throttle:user:{user_id}:hour"


def _get_mobile_key(mobile: str) -> str:
    return f"sms_throttle:mobile:{mobile}:hour"


def _get_global_key() -> str:
    return "sms_throttle:global:minute"


def check_sms_rate_limit(user_id: Optional[int] = None, mobile: Optional[str] = None) -> Tuple[bool, str]:
    """بررسی محدودیت نرخ برای ارسال پیامک.
    
    بازگشت: (مجاز است؟, دلیل عدم مجاز بودن)
    """
    if not SMS_RATE_LIMIT_ENABLED:
        return True, ""
    
    # بررسی محدودیت سراسری (تعداد کل پیامک‌های سیستم در دقیقه)
    global_count = cache.get(_get_global_key(), 0)
    if global_count >= SMS_RATE_LIMIT_GLOBAL_MINUTE:
        logger.warning(f"[SMS][THROTTLE] سیستم به حد کلی رسیده است: {global_count}/{SMS_RATE_LIMIT_GLOBAL_MINUTE} در دقیقه")
        return False, f"سیستم به حداکثر {SMS_RATE_LIMIT_GLOBAL_MINUTE} پیامک در دقیقه رسیده است؛ لطفاً کمی صبر کنید"
    
    # بررسی محدودیت هر کاربر
    if user_id:
        user_count = cache.get(_get_user_key(user_id), 0)
        if user_count >= SMS_RATE_LIMIT_PER_USER_HOUR:
            logger.warning(f"[SMS][THROTTLE] کاربر {user_id} به حد ساعتی رسید: {user_count}/{SMS_RATE_LIMIT_PER_USER_HOUR}")
            return False, f"شما به حداکثر {SMS_RATE_LIMIT_PER_USER_HOUR} پیامک در ساعت رسیده‌اید"
    
    # بررسی محدودیت هر شماره موبایل (برای شماره‌های دستی)
    if mobile:
        mobile_count = cache.get(_get_mobile_key(mobile), 0)
        if mobile_count >= SMS_RATE_LIMIT_PER_USER_HOUR:
            logger.warning(f"[SMS][THROTTLE] شماره {mobile} به حد ساعتی رسید: {mobile_count}/{SMS_RATE_LIMIT_PER_USER_HOUR}")
            return False, f"این شماره به حداکثر {SMS_RATE_LIMIT_PER_USER_HOUR} پیامک در ساعت رسیده است"
    
    return True, ""


def increment_sms_counters(user_id: Optional[int] = None, mobile: Optional[str] = None) -> None:
    """افزایش شمارنده‌های محدودیت نرخ بعد از ارسال موفق پیامک."""
    if not SMS_RATE_LIMIT_ENABLED:
        return
    
    # افزایش شمارنده سراسری (با TTL 60 ثانیه = 1 دقیقه)
    global_key = _get_global_key()
    try:
        current = cache.get(global_key, 0)
        cache.set(global_key, current + 1, timeout=60)
    except Exception as e:
        logger.error(f"[SMS][THROTTLE] خطا در افزایش شمارنده سراسری: {e}")
    
    # افزایش شمارنده کاربر (با TTL 3600 ثانیه = 1 ساعت)
    if user_id:
        user_key = _get_user_key(user_id)
        try:
            current = cache.get(user_key, 0)
            cache.set(user_key, current + 1, timeout=3600)
        except Exception as e:
            logger.error(f"[SMS][THROTTLE] خطا در افزایش شمارنده کاربر {user_id}: {e}")
    
    # افزایش شمارنده موبایل
    if mobile:
        mobile_key = _get_mobile_key(mobile)
        try:
            current = cache.get(mobile_key, 0)
            cache.set(mobile_key, current + 1, timeout=3600)
        except Exception as e:
            logger.error(f"[SMS][THROTTLE] خطا در افزایش شمارنده موبایل {mobile}: {e}")


__all__ = [
    'check_sms_rate_limit',
    'increment_sms_counters',
]
