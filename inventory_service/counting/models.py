from decimal import Decimal

from django.db import models

from inventory_service.core.base_models import BaseModel


class InventoryCount(BaseModel):
    COUNT_TYPES = [("full", "Full Count"), ("cycle", "Cycle Count"), ("spot", "Spot Check")]
    STATES = [("draft", "Draft"), ("in_progress", "In Progress"), ("done", "Done"), ("cancelled", "Cancelled")]

    corporate_id = models.UUIDField(db_index=True)
    reference = models.CharField(max_length=100, blank=True)
    count_type = models.CharField(max_length=20, choices=COUNT_TYPES, default="cycle")
    state = models.CharField(max_length=20, choices=STATES, default="draft")
    warehouse = models.ForeignKey("warehouse.Warehouse", on_delete=models.PROTECT)
    location = models.ForeignKey("warehouse.StorageLocation", on_delete=models.SET_NULL, null=True, blank=True)
    scheduled_date = models.DateField()
    done_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ["-scheduled_date"]

    def __str__(self):
        return f"{self.get_count_type_display()} — {self.scheduled_date}"


class InventoryCountLine(BaseModel):
    count = models.ForeignKey(InventoryCount, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    variant = models.ForeignKey("products.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey("warehouse.StorageLocation", on_delete=models.PROTECT)
    lot = models.ForeignKey("stock.StockLot", on_delete=models.SET_NULL, null=True, blank=True)
    expected_qty = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    counted_qty = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    difference = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    is_counted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.counted_qty is not None:
            self.difference = self.counted_qty - self.expected_qty
            self.is_counted = True
        super().save(*args, **kwargs)
