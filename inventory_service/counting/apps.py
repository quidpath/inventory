from django.apps import AppConfig


class CountingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory_service.counting"
    label = "counting"
