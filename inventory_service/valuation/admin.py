from django.contrib import admin

from .models import InventoryValuationReport, StockValuationLayer

admin.site.register(StockValuationLayer)
admin.site.register(InventoryValuationReport)
