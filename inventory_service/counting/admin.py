from django.contrib import admin

from .models import InventoryCount, InventoryCountLine


class InventoryCountLineInline(admin.TabularInline):
    model = InventoryCountLine
    extra = 0


@admin.register(InventoryCount)
class InventoryCountAdmin(admin.ModelAdmin):
    list_display = ["reference", "count_type", "state", "warehouse", "scheduled_date"]
    list_filter = ["count_type", "state"]
    inlines = [InventoryCountLineInline]
