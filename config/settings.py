"""
Django settings for moievent API.

Uses development defaults. Set ENVIRONMENT=prod and configure env vars for production.
"""
from datetime import timedelta
from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

AUTH_USER_MODEL = "accounts.User"

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_summernote',

    "core",
    "accounts",
    "authcodes",
    'category.apps.CategoryConfig',
    'book.apps.BookConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': config('DB_CONNECT_TIMEOUT', default=10, cast=int),
        },
        # Connection pooling settings for PostgreSQL
        'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),
    }
}

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = config('LANGUAGE_CODE', default='en-us')

TIME_ZONE = config('TIME_ZONE', default='UTC')

USE_I18N = True

USE_TZ = True

# Gemini API Key
GEMINI_API_KEY = config("GEMINI_API_KEY")


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# django-summernote settings (store uploads in MEDIA_ROOT)
SUMMERNOTE_CONFIG = {
    "attachment_upload_to": "summernote",
    "attachment_filesize_limit": 5 * 1024 * 1024,  # 5MB
}


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Environment
ENVIRONMENT = config('ENVIRONMENT', default='dev')
IS_PRODUCTION = ENVIRONMENT.lower() == 'prod'

# Security (must be after IS_PRODUCTION)
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-x0d3^sfe!y7$#s@ot1gl#+iso#*fzzum7$47ndd&voh=cjtyn3' if not IS_PRODUCTION else None,
)
if IS_PRODUCTION and (not SECRET_KEY or SECRET_KEY == 'change-me-to-a-long-random-value'):
    raise ValueError('SECRET_KEY must be set in production.')
DEBUG = config('DEBUG', default=not IS_PRODUCTION, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    ALLOWED_HOSTS = [] if IS_PRODUCTION else ['localhost', '127.0.0.1']

# CORS
_cors_origins_raw = config(
    'CORS_ALLOWED_ORIGINS',
    default='' if IS_PRODUCTION else 'http://localhost:5173,http://localhost:3000',
    cast=Csv(),
)
CORS_ALLOWED_ORIGINS = [x.strip() for x in _cors_origins_raw if x and x.strip()]
CORS_ALLOW_CREDENTIALS = config('CORS_ALLOW_CREDENTIALS', default=not IS_PRODUCTION, cast=bool)
CORS_ALLOW_METHODS = ['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']

_csrf_origins_raw = config(
    'CSRF_TRUSTED_ORIGINS',
    default='' if IS_PRODUCTION else 'http://localhost:5173,http://localhost:3000',
    cast=Csv(),
)
CSRF_TRUSTED_ORIGINS = [x.strip() for x in _csrf_origins_raw if x and x.strip()]


# Django REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'authcodes.authentication.CodeJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        # Changed to AllowAny by default, views will specify their own permissions
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 15,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10000/hour' if DEBUG else '100/hour',
        'user': '10000/hour' if DEBUG else '1000/hour',
        'code_login': '10/minute',
        'admin_login': '10/minute',
    },
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}


# Simple JWT Settings
SIMPLE_JWT = {
    # Super Admin tokens (longer lived)
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=config('JWT_REFRESH_TOKEN_LIFETIME', default=7, cast=int)
    ),

    # Token settings
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    # Algorithm
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    # Token types
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    # Token validation
    'AUTH_TOKEN_CLASSES': (
        'rest_framework_simplejwt.tokens.AccessToken',
        'authcodes.tokens.CodeAccessToken',
    ),
    'TOKEN_TYPE_CLAIM': 'token_type',

    # Sliding token settings (not used, but good to have)
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}


# Authentication Code Settings
AUTH_CODE_TOKEN_LIFETIME_MINUTES = config(
    'AUTH_CODE_TOKEN_LIFETIME_MINUTES',
    default=30,
    cast=int
)
CODE_EXPIRATION_HOURS = config('CODE_EXPIRATION_HOURS', default=48, cast=int)


# Production-specific security settings
if IS_PRODUCTION:
    # Security settings for production
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)

    # Static files for production
    STATIC_ROOT = config('STATIC_ROOT', default=BASE_DIR / 'staticfiles')
    STATIC_URL = config('STATIC_URL', default='/static/')
    MEDIA_ROOT = config('MEDIA_ROOT', default=BASE_DIR / 'media')
    MEDIA_URL = config('MEDIA_URL', default='/media/')

# Celery Configuration for Background Video Processing
# Redis is used as the broker and result backend
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 3600  # 1 hour max for video processing
CELERY_TASK_SOFT_TIME_LIMIT = 3540  # Soft limit at 59 minutes

# Cache configuration
# Use Redis when REDIS_ENABLED=true, otherwise fall back to local memory cache.
REDIS_ENABLED = config('REDIS_ENABLED', default=False, cast=bool)
REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/1')

if REDIS_ENABLED:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'moievent-local-cache',
        }
    }
