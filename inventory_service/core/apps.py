from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory_service.core"
    label = "inventory_core"
    verbose_name = "Core (base models, utils, services)"
