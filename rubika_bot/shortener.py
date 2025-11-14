"""
سیستم کوتاه‌کننده لینک برای کدهای اتصال روبیکا
"""
import hashlib
from django.core.cache import cache


def generate_short_code(connection_code: str) -> str:
    """
    تولید کد کوتاه 4 کاراکتری از کد اتصال 32 کاراکتری
    از hash استفاده می‌کنیم تا همیشه یکسان باشد
    """
    # استفاده از 4 کاراکتر اول از MD5 hash برای لینک خیلی کوتاه
    hash_obj = hashlib.md5(connection_code.encode())
    short_code = hash_obj.hexdigest()[:4]
    return short_code


def save_short_link(short_code: str, connection_code: str, ttl_minutes: int = 60) -> None:
    """
    ذخیره mapping بین کد کوتاه و کد کامل در cache
    """
    cache_key = f"short_link:{short_code}"
    cache.set(cache_key, connection_code, timeout=ttl_minutes * 60)


def get_connection_code_from_short(short_code: str) -> str:
    """
    دریافت کد کامل اتصال از روی کد کوتاه
    """
    cache_key = f"short_link:{short_code}"
    return cache.get(cache_key)


def create_short_link(connection_code: str, bot_username: str) -> str:
    """
    ایجاد لینک کوتاه برای کد اتصال
    
    Returns:
        لینک کوتاه به فرمت: mkt.ir/c/ab12 (13 کاراکتر)
    """
    short_code = generate_short_code(connection_code)
    save_short_link(short_code, connection_code, ttl_minutes=60)
    
    # لینک فوق‌العاده کوتاه (اگر دامنه کوتاه‌تری داری)
    # برای الان از miepcoj.ir استفاده می‌کنیم
    short_url = f"miepcoj.ir/c/{short_code}"
    
    return short_url
