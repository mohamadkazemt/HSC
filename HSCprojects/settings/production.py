# HSCprojects/settings/production.py

# 1. ابتدا تمام تنظیمات پایه را وارد کن
from .base import *
import os
from decouple import config

# 2. حالا تنظیمات مخصوص production را بازنویسی کن

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# SECURITY WARNING: keep the secret key used in production secret!
# این کلید باید از فایل .env خوانده شود
SECRET_KEY = config('SECRET_KEY')

# هاست‌های مجاز برای سرور تولید
ALLOWED_HOSTS = [
    't.miepcoj.ir',
    'mtorkzadeh.ir',
    'www.mtorkzadeh.ir',
    'miepcoj.ir',
    'www.miepcoj.ir',
    'localhost', # برای تست‌های داخلی سرور
    '65.109.220.72'
    '65.109.190.172'
]

# تنظیمات دیتابیس PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432', cast=int),
    }
}

# تنظیمات فایل‌های استاتیک برای تولید
# مسیر STATIC_ROOT را از base.py برمی‌داریم و اینجا تعریف می‌کنیم
STATIC_ROOT = '/var/www/HSC/static/'
STATICFILES_DIRS = []  # در تولید، این باید خالی باشد.

# تنظیمات امنیتی HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 سال
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# تنظیمات لاگ‌گیری برای تولید
# لاگ‌گیری موجود در base.py برای تولید مناسب است، پس می‌توانیم آن را بازنویسی نکنیم
# یا می‌توانیم یک نسخه ساده‌تر برای تولید تعریف کنیم:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {module}:{lineno} | {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING', # فقط خطاها و هشدارها را لاگ کن
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'production.log'),
            'when': 'midnight',
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}


RATELIMIT_IP_META_KEY = 'HTTP_X_FORWARDED_FOR'

# تنظیمات ایمیل برای تولید
# این بخش را فقط در صورتی که ایمیل SMTP دارید کامل کنید
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = config('EMAIL_HOST')
# EMAIL_PORT = config('EMAIL_PORT', cast=int)
# EMAIL_HOST_USER = config('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
# EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=True)

# و تمام! بقیه تنظیمات از base.py خوانده می‌شوند.