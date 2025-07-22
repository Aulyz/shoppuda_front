# File: shopuda/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-shopuda-erp-secret-key-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    'django_filters',
    'crispy_forms',
    'crispy_tailwind',
    'django.contrib.humanize',
    'mathfilters',
    
    # Local apps
    'accounts',  # accounts를 맨 처음에 두어 User 모델이 먼저 등록되도록 함
    'core',
    'dashboard',
    'products',
    'orders',
    'inventory',
    'platforms',
    'api',
    'reports',
    'channels',
    'notifications',
    'search',
    'shop',  # 사용자용 쇼핑몰 앱

    # Custom tags
    'products.templatetags.product_tags',
    'inventory.templatetags.inventory_extras',
    'dashboard.templatetags.dateformat',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.MaintenanceModeMiddleware',  # 유지보수 모드 미들웨어
    'core.middleware.AdminAccessMiddleware',  # 관리자 접근 제어 미들웨어
]

ROOT_URLCONF = 'shopuda.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.user_permissions',
                'core.context_processors.system_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'shopuda.wsgi.application'

# Database - SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# Password validation
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
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Cache - Django 기본 캐시 (개발용)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'shopuda-cache',
    }
}

# Session
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'jonghwan3363@gmail.com'
EMAIL_HOST_PASSWORD = 'qjetijdabuflrpua'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
google_pw = 'qjet ijda bufl rpua'

# Celery 설정 (Redis 없이 Django DB 사용)
CELERY_BROKER_URL = 'django://'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat 스케줄
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'sync-all-platforms': {
        'task': 'platforms.tasks.sync_all_platforms',
        'schedule': crontab(minute=0, hour='*/6'),  # 6시간마다
    },
    'low-stock-alert': {
        'task': 'platforms.tasks.generate_low_stock_alert',
        'schedule': crontab(minute=0, hour=9),  # 매일 오전 9시
    },
    'cleanup-sync-logs': {
        'task': 'platforms.tasks.cleanup_old_sync_logs',
        'schedule': crontab(minute=0, hour=2, day_of_week=1),  # 매주 월요일 오전 2시
    },
    'health-check': {
        'task': 'platforms.tasks.health_check',
        'schedule': crontab(minute='*/30'),  # 30분마다
    },
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'platforms.tasks': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# 로그 디렉토리 생성
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Platform API settings
PLATFORM_SYNC_INTERVAL = 300  # 5분마다 동기화

# 관리자 설정
ADMINS = [
    ('관리자', 'admin@shopuda.com'),
]

# 슬랙 웹훅 URL (선택사항)
# SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

# Authentication 설정
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Session 설정
SESSION_COOKIE_AGE = 3600 * 24 * 7  # 7일
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

CSRF_COOKIE_SECURE = False  # 개발환경에서는 False, 프로덕션에서는 True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

# AJAX 요청을 위한 CSRF 설정
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'

# 재고 알림 이메일 설정
ENABLE_STOCK_EMAIL_ALERTS = True
STOCK_ALERT_RECIPIENTS = ['shopuda@naver.com']

# Channels 설정
ASGI_APPLICATION = 'shopuda.asgi.application'

# Redis 설정 (채널 레이어용)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('0.0.0.0', 6379)],
        },
    },
}

NOTIFICATION_SETTINGS = {
    'BATCH_SIZE': 100,  # 한 번에 처리할 알림 수
    'RETENTION_DAYS': 30,  # 알림 보관 기간 (일)
    'REAL_TIME_ENABLED': True,  # 실시간 알림 활성화
}

# 검색 설정
SEARCH_SETTINGS = {
    'RESULTS_PER_PAGE': 20,  # 페이지당 검색 결과 수
    'QUICK_SEARCH_LIMIT': 5,  # 빠른 검색 결과 수
    'MIN_SEARCH_LENGTH': 2,  # 최소 검색어 길이
}


CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}