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
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from django.conf.locale.fa import formats as fa_formats



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ygf6#b*bj-ko2fimc)sg=u2vo6c)5a1#c5#zr=@#8&o7nd*tpt'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1','mtorkzadeh.ir','miepcoj.ir', 'localhost']


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


    "django_select2",
    'analytics.apps.AnalyticsConfig',
    'crispy_forms',
    'crispy_bootstrap5',
    'shift_manager.apps.ShiftManagerConfig',
    'django_jalali',
    'jalali_date',
    'import_export',
    'BaseInfo.apps.BaseinfoConfig',
    'OperationsShiftReports.apps.OperationsshiftreportsConfig',
    'formtools',
    'dailyreport_hse.apps.DailyreportHseConfig',
    'leave_reports.apps.LeaveReportsConfig',
    'contractor_management.apps.ContractorManagementConfig',
    'rest_framework',
    'permissions.apps.PermissionsConfig',
    'hse_incidents.apps.HseIncidentsConfig',
    'machine_checklist.apps.MachineChecklistConfig'

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
            'builtins': [
                'django_jalali.templatetags.jformat',

            ],
        },
    },
]

WSGI_APPLICATION = 'HSCprojects.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'hsc_db',
            'USER': 'hsc_user',
            'PASSWORD': 'Znmk@0900',
            'HOST': 'localhost',
            'PORT': '5432',
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
SMSIR_API_KEY = 'gCLhWKiCoUXwUQiNBIXCpQ81IiGfujNmKgWyrQr19WwgDkv3dSfFSDgIbsSEoo03'
SMSIR_LINE_NUMBER = '30007732001185'




fa_formats.DATETIME_FORMAT = "Y/m/d H:i"
fa_formats.DATE_FORMAT = "Y/m/d"



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
           'level': 'DEBUG',
           'class': 'logging.FileHandler',
           'filename': 'hse_incidents.log',
        },
    },
    'loggers': {
        'hse_incidents': {
            'handlers': ['console','file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}



JALALI_DATE_DEFAULTS = {
   # if change it to true then all dates of the list_display will convert to the Jalali.
   'LIST_DISPLAY_AUTO_CONVERT': False,
   'Strftime': {
        'date': '%y/%m/%d',
        'datetime': '%H:%M:%S _ %y/%m/%d',
    },
    'Static': {
        'js': [
            # loading datepicker
            'admin/js/django_jalali.min.js',
            # OR
            # 'admin/jquery.ui.datepicker.jalali/scripts/jquery.ui.core.js',
            # 'admin/jquery.ui.datepicker.jalali/scripts/calendar.js',
            # 'admin/jquery.ui.datepicker.jalali/scripts/jquery.ui.datepicker-cc.js',
            # 'admin/jquery.ui.datepicker.jalali/scripts/jquery.ui.datepicker-cc-fa.js',
            # 'admin/js/main.js',
        ],
        'css': {
            'all': [
                'admin/jquery.ui.datepicker.jalali/themes/base/jquery-ui.min.css',
            ]
        }
    },
}