from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from inventory_service.core.base_models import BaseModel


class StockLot(BaseModel):
    """Batch / lot tracking."""
    corporate_id = models.UUIDField(db_index=True)
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT, related_name="lots")
    lot_number = models.CharField(max_length=150, db_index=True)
    expiry_date = models.DateField(null=True, blank=True)
    manufacture_date = models.DateField(null=True, blank=True)
    supplier_lot = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("corporate_id", "product", "lot_number")]

    def __str__(self):
        return f"{self.product.name} — Lot {self.lot_number}"

    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False


class SerialNumber(BaseModel):
    STATES = [("available", "Available"), ("used", "In Use"), ("returned", "Returned"), ("scrapped", "Scrapped")]

    corporate_id = models.UUIDField(db_index=True)
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT, related_name="serials")
    variant = models.ForeignKey("products.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True)
    serial_number = models.CharField(max_length=200, db_index=True)
    state = models.CharField(max_length=20, choices=STATES, default="available")
    location = models.ForeignKey("warehouse.StorageLocation", on_delete=models.SET_NULL, null=True, blank=True)
    lot = models.ForeignKey(StockLot, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [("corporate_id", "product", "serial_number")]

    def __str__(self):
        return f"{self.product.name} SN:{self.serial_number}"


class StockLevel(BaseModel):
    """
    Denormalized current stock quantity per product variant per location.
    Updated on every stock move confirmation.
    """
    corporate_id = models.UUIDField(db_index=True)
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="stock_levels")
    variant = models.ForeignKey("products.ProductVariant", on_delete=models.CASCADE, null=True, blank=True)
    location = models.ForeignKey("warehouse.StorageLocation", on_delete=models.CASCADE, related_name="stock_levels")
    lot = models.ForeignKey(StockLot, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    reserved_quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        unique_together = [("corporate_id", "product", "variant", "location", "lot")]

    def __str__(self):
        return f"{self.product.name} @ {self.location.name}: {self.quantity}"

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity


class ReorderRule(BaseModel):
    """Auto-generate purchase requisition when stock falls below min_qty."""
    corporate_id = models.UUIDField(db_index=True)
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="reorder_rules")
    variant = models.ForeignKey("products.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey("warehouse.StorageLocation", on_delete=models.SET_NULL, null=True, blank=True)
    min_qty = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    max_qty = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    reorder_qty = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Reorder: {self.product.name} min={self.min_qty}"


class StockMove(BaseModel):
    """Every stock movement — immutable audit trail."""
    MOVE_TYPES = [
        ("receipt", "Receipt from Vendor"),
        ("delivery", "Delivery to Customer"),
        ("transfer", "Internal Transfer"),
        ("adjustment", "Inventory Adjustment"),
        ("scrap", "Scrap"),
        ("return_vendor", "Return to Vendor"),
        ("return_customer", "Return from Customer"),
        ("initial", "Initial Stock"),
        ("production_in", "Production Input"),
        ("production_out", "Production Output"),
    ]
    STATES = [
        ("draft", "Draft"),
        ("confirmed", "Confirmed"),
        ("assigned", "Stock Assigned"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ]

    corporate_id = models.UUIDField(db_index=True)
    reference = models.CharField(max_length=200, blank=True, db_index=True, help_text="PO/SO/Ref number")
    move_type = models.CharField(max_length=30, choices=MOVE_TYPES)
    state = models.CharField(max_length=20, choices=STATES, default="draft")
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT, related_name="stock_moves")
    variant = models.ForeignKey("products.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True)
    lot = models.ForeignKey(StockLot, on_delete=models.SET_NULL, null=True, blank=True)
    serial = models.ForeignKey(SerialNumber, on_delete=models.SET_NULL, null=True, blank=True)
    location_from = models.ForeignKey(
        "warehouse.StorageLocation", on_delete=models.PROTECT,
        related_name="moves_from", null=True, blank=True
    )
    location_to = models.ForeignKey(
        "warehouse.StorageLocation", on_delete=models.PROTECT,
        related_name="moves_to", null=True, blank=True
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))])
    uom = models.ForeignKey("products.UnitOfMeasure", on_delete=models.PROTECT)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    done_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_move_type_display()} | {self.product.name} x{self.quantity}"

    @transaction.atomic
    def confirm(self):
        if self.state != "draft":
            raise ValueError("Only draft moves can be confirmed")
        self.state = "assigned"
        self.save()

    @transaction.atomic
    def validate(self):
        """Mark move as done and update stock levels."""
        if self.state not in ("confirmed", "assigned"):
            raise ValueError("Move must be confirmed before validation")

        # Decrement source
        if self.location_from and self.location_from.location_type == "internal":
            sl_from, _ = StockLevel.objects.get_or_create(
                corporate_id=self.corporate_id,
                product=self.product,
                variant=self.variant,
                location=self.location_from,
                lot=self.lot,
                defaults={"quantity": Decimal("0")},
            )
            sl_from.quantity -= self.quantity
            sl_from.save()

        # Increment destination
        if self.location_to and self.location_to.location_type == "internal":
            sl_to, _ = StockLevel.objects.get_or_create(
                corporate_id=self.corporate_id,
                product=self.product,
                variant=self.variant,
                location=self.location_to,
                lot=self.lot,
                defaults={"quantity": Decimal("0")},
            )
            sl_to.quantity += self.quantity
            sl_to.save()

        self.state = "done"
        self.done_date = timezone.now()
        self.save()
