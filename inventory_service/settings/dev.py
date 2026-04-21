from .base import *
import dj_database_url
import os

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Service URLs for development environment
ERP_BACKEND_URL = os.environ.get("ERP_BACKEND_URL", "http://quidpath-backend-dev:8004")
POS_SERVICE_URL = os.environ.get("POS_SERVICE_URL", "http://pos-backend-dev:8000")
CRM_SERVICE_URL = os.environ.get("CRM_SERVICE_URL", "http://crm-backend-dev:8000")
HRM_SERVICE_URL = os.environ.get("HRM_SERVICE_URL", "http://hrm-backend-dev:8000")
PROJECTS_SERVICE_URL = os.environ.get("PROJECTS_SERVICE_URL", "http://projects-backend-dev:8007")

# Use DATABASE_URL from environment if provided (Docker), otherwise use default local config
if os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ.get("DATABASE_URL"),
            conn_max_age=600,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "devdb",
            "USER": "devuser",
            "PASSWORD": "devpass",
            "HOST": "db",
            "PORT": "5432",
        }
    }

CORS_ALLOW_ALL_ORIGINS = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "DEBUG"},
}
