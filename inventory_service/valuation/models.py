from decimal import Decimal

from django.db import models

from inventory_service.core.base_models import BaseModel


class StockValuationLayer(BaseModel):
    """
    FIFO/AVCO valuation layer.
    Each receipt creates a layer. Delivery consumes layers in FIFO order.
    """
    corporate_id = models.UUIDField(db_index=True)
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="valuation_layers")
    variant = models.ForeignKey("products.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True)
    stock_move = models.ForeignKey("stock.StockMove", on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    remaining_qty = models.DecimalField(max_digits=18, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4)
    total_value = models.DecimalField(max_digits=22, decimal_places=4)
    description = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.product.name} qty={self.quantity} cost={self.unit_cost}"


class InventoryValuationReport(BaseModel):
    """Snapshot of total inventory value at a point in time."""
    corporate_id = models.UUIDField(db_index=True)
    report_date = models.DateField()
    total_value = models.DecimalField(max_digits=22, decimal_places=4, default=Decimal("0"))
    currency = models.CharField(max_length=3, default="KES")
    lines = models.JSONField(default=list)

    class Meta:
        ordering = ["-report_date"]

    def __str__(self):
        return f"Valuation Report {self.report_date} — {self.currency} {self.total_value}"
