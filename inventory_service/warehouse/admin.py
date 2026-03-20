from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from .models import StorageLocation, Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ["name", "short_name", "city", "is_active"]
    search_fields = ["name", "short_name"]


admin.site.register(StorageLocation, MPTTModelAdmin)
