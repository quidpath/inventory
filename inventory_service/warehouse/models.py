from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

from inventory_service.core.base_models import BaseModel


class Warehouse(BaseModel):
    corporate_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=10, help_text="Used as prefix for location codes")
    address_line1 = models.CharField(max_length=300, blank=True)
    address_line2 = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="Kenya")
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("corporate_id", "short_name")]

    def __str__(self):
        return self.name


class StorageLocation(MPTTModel):
    """
    Hierarchical storage location.
    e.g. WH1 > Zone A > Shelf 1 > Bin 01
    MPTTModel incompatible with BaseModel; timestamps added manually.
    """
    LOCATION_TYPES = [
        ("internal", "Internal"),
        ("vendor", "Vendor"),
        ("customer", "Customer"),
        ("transit", "Transit"),
        ("virtual", "Virtual / Loss"),
        ("scrap", "Scrap"),
    ]

    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="locations", null=True, blank=True)
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    name = models.CharField(max_length=200)
    complete_name = models.CharField(max_length=500, blank=True)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES, default="internal")
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    is_active = models.BooleanField(default=True)
    posx = models.IntegerField(default=0, help_text="Corridor")
    posy = models.IntegerField(default=0, help_text="Shelves")
    posz = models.IntegerField(default=0, help_text="Height")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ["name"]

    class Meta:
        ordering = ["complete_name"]

    def __str__(self):
        return self.complete_name or self.name

    def save(self, *args, **kwargs):
        if self.parent:
            self.complete_name = f"{self.parent.complete_name}/{self.name}"
        else:
            self.complete_name = self.name
        super().save(*args, **kwargs)
