import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_service.settings.prod")

app = Celery("inventory_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
