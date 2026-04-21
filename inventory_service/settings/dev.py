from .base import *
import dj_database_url
import os

DEBUG = True
ALLOWED_HOSTS = ["*"]

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
