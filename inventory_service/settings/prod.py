import os

from corsheaders.defaults import default_headers

from .base import *

print("Using Production Settings")

if os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ.get("DATABASE_URL"),
            conn_max_age=600,
        )
    }
    DATABASES["default"]["OPTIONS"] = {"sslmode": "disable"}
else:
    _user = os.getenv("POSTGRES_USER")
    _db = os.getenv("POSTGRES_DB")
    if not _user or not _db:
        raise ValueError(
            "Production requires DATABASE_URL or both POSTGRES_USER and POSTGRES_DB."
        )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _db,
            "USER": _user,
            "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
            "HOST": os.getenv("DB_HOST", "db"),
            "PORT": "5432",
            "OPTIONS": {"sslmode": "disable"},
        },
    }

DEBUG = False

_default_hosts = "inventory.quidpath.com,api.quidpath.com,quidpath.com,localhost,127.0.0.1,0.0.0.0"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", _default_hosts).split(",") if h.strip()]
if "inventory-backend" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("inventory-backend")

_env_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
if _env_csrf:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _env_csrf.split(",") if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = ["https://quidpath.com", "https://www.quidpath.com", "https://*.quidpath.com"]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = ["https://quidpath.com", "https://www.quidpath.com"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = list(default_headers) + ["authorization", "content-type"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
