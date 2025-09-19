from django.core.cache import cache, caches
from django.core.cache.utils import make_template_fragment_key
from django.conf import settings
from functools import wraps
import json
import hashlib
import logging
from typing import Any, Optional, Callable

logger = logging.getLogger(__name__)

def get_safe_cache():
    """
    دریافت cache امن - در صورت خطا از fallback استفاده می‌کند
    """
    try:
        # تست اتصال cache اصلی
        cache.get('test_connection')
        return cache
    except Exception as e:
        logger.warning(f'Redis cache connection failed, using fallback: {e}')
        try:
            return caches['fallback']
        except:
            logger.error('All cache backends failed, using dummy cache')
            return caches['default']


def cache_key_generator(*args, **kwargs) -> str:
    """
    تولید کلید کش بر اساس آرگومان‌ها
    """
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items()) if kwargs else {}
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_function(timeout: int = 300, key_prefix: str = None):
    """
    دکوریتور برای کش کردن نتیجه توابع
    
    Usage:
    @cache_function(timeout=600, key_prefix='user_data')
    def get_user_statistics(user_id):
        return expensive_calculation(user_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # تولید کلید کش
            func_name = f"{func.__module__}.{func.__name__}"
            if key_prefix:
                cache_key = f"{key_prefix}:{func_name}:{cache_key_generator(*args, **kwargs)}"
            else:
                cache_key = f"{func_name}:{cache_key_generator(*args, **kwargs)}"
            
            # بررسی وجود در کش
            safe_cache = get_safe_cache()
            cached_result = safe_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # اجرای تابع و کش کردن نتیجه
            result = func(*args, **kwargs)
            try:
                safe_cache.set(cache_key, result, timeout)
            except Exception as e:
                logger.warning(f'Failed to cache result for {func.__name__}: {e}')
            return result
        # aضافه کردن متد clear_cache
        wrapper.clear_cache = lambda *args, **kwargs: get_safe_cache().delete(
            f"{key_prefix or ''}:{func.__module__}.{func.__name__}:{cache_key_generator(*args, **kwargs)}"
        )
        )
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str) -> int:
    """
    حذف تمام کلیدهای کش که با pattern مطابقت دارند
    """
    from django_redis import get_redis_connection
    
    try:
        redis_conn = get_redis_connection("default")
        keys = redis_conn.keys(f"*{pattern}*")
        if keys:
            return redis_conn.delete(*keys)
        return 0
    except Exception:
        # fallback to Django cache
        return 0


def cache_model_instance(model_instance, timeout: int = 3600) -> str:
    """
    کش کردن instance مدل
    """
    model_name = model_instance.__class__.__name__
    cache_key = f"model:{model_name}:{model_instance.pk}"
    try:
        get_safe_cache().set(cache_key, model_instance, timeout)
    except Exception as e:
        logger.warning(f'Failed to cache model instance: {e}')
    return cache_key


def get_cached_model_instance(model_class, pk: int) -> Optional[Any]:
    """
    دریافت instance مدل از کش
    """
    model_name = model_class.__name__
    cache_key = f"model:{model_name}:{pk}"
    try:
        return get_safe_cache().get(cache_key)
    except Exception as e:
        logger.warning(f'Failed to get cached model instance: {e}')
        return None


def cache_page_fragments():
    """
    کمک‌کننده برای کش کردن بخش‌های template
    """
    def cache_fragment(fragment_name: str, vary_on: list = None, timeout: int = 300):
        """
        Usage in template:
        {% load cache %}
        {% cache 300 sidebar request.user.username %}
            <!-- expensive template code -->
        {% endcache %}
        """
        if vary_on is None:
            vary_on = []
        
        cache_key = make_template_fragment_key(fragment_name, vary_on)
        return cache_key
    
    return cache_fragment


class CacheManager:
    """
    مدیریت مرکزی کش
    """
    
    @staticmethod
    def warm_up_cache():
        """
        پیش‌بارگذاری کش‌های مهم
        """
        # اینجا می‌توانید کش‌های مهم سیستم را پیش‌بارگذاری کنید
        pass
    
    @staticmethod
    def clear_all_cache():
        """
        پاک کردن تمام کش
        """
        try:
            get_safe_cache().clear()
        except Exception as e:
            logger.error(f'Failed to clear cache: {e}')
    
    @staticmethod
    def get_cache_stats():
        """
        دریافت آمار کش
        """
        from django_redis import get_redis_connection
        
        try:
            redis_conn = get_redis_connection("default")
            info = redis_conn.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'N/A'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_ratio': round(
                    info.get('keyspace_hits', 0) / 
                    (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)) * 100, 2
                )
            }
        except Exception:
            return {'error': 'Unable to connect to Redis'}


# مثال‌های استفاده
@cache_function(timeout=1800, key_prefix='user_stats')
def get_user_shift_statistics(user_id: int):
    """
    دریافت آمار شیفت کاربر (کش می‌شود برای 30 دقیقه)
    """
    # کد پردازش آمار...
    pass


@cache_function(timeout=3600, key_prefix='mining_data')
def get_mining_block_status():
    """
    دریافت وضعیت بلوک‌های معدنی (کش می‌شود برای 1 ساعت)
    """
    # کد پردازش داده‌های معدنی...
    pass