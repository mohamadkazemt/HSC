"""
Django settings for HSCprojects project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
import os
from pathlib import Path



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ygf6#b*bj-ko2fimc)sg=u2vo6c)5a1#c5#zr=@#8&o7nd*tpt'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "dashboard.apps.DashboardConfig",
    "accounts.apps.AccountsConfig",
    "anomalis.apps.AnomalisConfig",
    'django.contrib.humanize',

    'taggit',
    "django_select2",
    'analytics.apps.AnalyticsConfig',
    'crispy_forms',
    'crispy_bootstrap5',
    'shift_manager.apps.ShiftManagerConfig',
    'django_jalali',
    'import_export',
    'BaseInfo.apps.BaseinfoConfig',
    'OperationsShiftReports.apps.OperationsshiftreportsConfig',
    'formtools',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'HSCprojects.urls'
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.user_profile_processor',
                'analytics.context_processors.anomaly_stats_context',
                'dashboard.context_processors.notification_context_processor',
                'shift_manager.context_processors.shift_context_processor',
                'shift_manager.context_processors.shift_data_processor',

            ],
        },
    },
]

WSGI_APPLICATION = 'HSCprojects.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

#DATABASES = {
        #'default': {
        #    'ENGINE': 'django.db.backends.postgresql',
       #     'NAME': 'hsc_db',
      #      'USER': 'hsc_user',
     #       'PASSWORD': 'Znmk@0900',
    #        'HOST': 'localhost',
   #         'PORT': '5432',
  #      }
 #   }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'fa-ir'

TIME_ZONE = 'Asia/Tehran'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    BASE_DIR / "static"
]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')



# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = '/dashboard/'

# ارسال پیامک
SMS_API_KEY = 'gCLhWKiCoUXwUQiNBIXCpQ81IiGfujNmKgWyrQr19WwgDkv3dSfFSDgIbsSEoo03'
SMS_LINE_NUMBER = '30007732001185'


# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}