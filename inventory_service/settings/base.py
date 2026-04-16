import os
from pathlib import Path

import dj_database_url
from corsheaders.defaults import default_headers
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

ENV_FILE = BASE_DIR / (".env.dev" if os.environ.get("DJANGO_ENV") == "dev" else ".env")
load_dotenv(ENV_FILE)

SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-dev-key")
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "mptt",
    "django_celery_beat",
    "django_celery_results",
    "inventory_service.core",
    "inventory_service.audit",
    "inventory_service.products.apps.ProductsConfig",
    "inventory_service.warehouse.apps.WarehouseConfig",
    "inventory_service.stock.apps.StockConfig",
    "inventory_service.valuation.apps.ValuationConfig",
    "inventory_service.counting.apps.CountingConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "inventory_service.middleware.jwt_auth.JWTAuthenticationMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "inventory_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "inventory_service.wsgi.application"

def _build_database_url():
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    # Fall back to constructing from individual parts
    user = os.environ.get("POSTGRES_USER", "")
    password = os.environ.get("POSTGRES_PASSWORD", "")
    host = os.environ.get("POSTGRES_HOST", "db")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


DATABASES = {
    "default": dj_database_url.config(
        default=_build_database_url(),
        conn_max_age=600,
    )
}

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)

# Service URLs for integration
ERP_BACKEND_URL = os.environ.get("ERP_BACKEND_URL", "http://django-backend:8000")
POS_SERVICE_URL = os.environ.get("POS_SERVICE_URL", "http://pos-backend:8000")
CRM_SERVICE_URL = os.environ.get("CRM_SERVICE_URL", "http://crm-backend:8000")
HRM_SERVICE_URL = os.environ.get("HRM_SERVICE_URL", "http://hrm-backend:8000")
PROJECTS_SERVICE_URL = os.environ.get("PROJECTS_SERVICE_URL", "http://projects-backend:8000")

# Service authentication - own secret
INVENTORY_SERVICE_SECRET = os.environ.get("INVENTORY_SERVICE_SECRET", "")
# Cross-service secrets (used when calling other services)
ERP_SERVICE_SECRET = os.environ.get("ERP_SERVICE_SECRET", "")
POS_SERVICE_SECRET = os.environ.get("POS_SERVICE_SECRET", "")
CRM_SERVICE_SECRET = os.environ.get("CRM_SERVICE_SECRET", "")
HRM_SERVICE_SECRET = os.environ.get("HRM_SERVICE_SECRET", "")
PROJECTS_SERVICE_SECRET = os.environ.get("PROJECTS_SERVICE_SECRET", "")
BILLING_SERVICE_SECRET = os.environ.get("BILLING_SERVICE_SECRET", "")
# Legacy alias — kept for backward compatibility
SERVICE_API_KEY = ERP_SERVICE_SECRET or INVENTORY_SERVICE_SECRET

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Africa/Nairobi"

USER_CACHE_TTL = int(os.environ.get("USER_CACHE_TTL", 3600))
CORPORATE_CACHE_TTL = int(os.environ.get("CORPORATE_CACHE_TTL", 86400))

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "https://quidpath.com",
    "https://www.quidpath.com",
    "http://localhost:3000",
]
CORS_ALLOW_HEADERS = list(default_headers) + ["authorization"]
