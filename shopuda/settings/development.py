"""
Development settings for Shopuda project.
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Database - SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_ALL_ORIGINS = True  # Only for development

# Security settings for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

# Email backend for development (console output)
if not config('EMAIL_HOST_USER', default=''):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Debug toolbar (optional - install separately if needed)
# if DEBUG:
#     INSTALLED_APPS += ['debug_toolbar']
#     MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
#     INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Channels - In-memory layer for development
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}