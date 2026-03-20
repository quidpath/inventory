from django.contrib import admin

from .models import ReorderRule, SerialNumber, StockLevel, StockLot, StockMove


@admin.register(StockMove)
class StockMoveAdmin(admin.ModelAdmin):
    list_display = ["reference", "move_type", "state", "product", "quantity", "created_at"]
    list_filter = ["move_type", "state"]
    search_fields = ["reference", "product__name"]


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ["product", "location", "quantity", "reserved_quantity", "updated_at"]
    search_fields = ["product__name"]


admin.site.register(StockLot)
admin.site.register(SerialNumber)
admin.site.register(ReorderRule)
