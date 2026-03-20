from django.core.validators import MinValueValidator
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

from inventory_service.core.base_models import BaseModel


class Category(MPTTModel):
    """Hierarchical product category tree. MPTTModel incompatible with BaseModel; timestamps added manually."""
    corporate_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ["name"]

    class Meta:
        verbose_name_plural = "categories"
        unique_together = [("corporate_id", "slug")]

    def __str__(self):
        return self.name


class UnitOfMeasureCategory(BaseModel):
    """e.g. Weight, Length, Volume, Time, Unit"""
    corporate_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "UoM categories"

    def __str__(self):
        return self.name


class UnitOfMeasure(BaseModel):
    ROUNDING_CHOICES = [("UP", "Up"), ("DOWN", "Down"), ("HALF_UP", "Half Up")]

    corporate_id = models.UUIDField(db_index=True)
    category = models.ForeignKey(UnitOfMeasureCategory, on_delete=models.PROTECT, related_name="uoms")
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    factor = models.DecimalField(
        max_digits=20, decimal_places=10, default=1,
        help_text="Multiplier to convert to base UoM of the category"
    )
    rounding = models.CharField(max_length=10, choices=ROUNDING_CHOICES, default="HALF_UP")
    is_base = models.BooleanField(default=False, help_text="Reference unit for the category")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Unit of Measure"
        unique_together = [("corporate_id", "name")]

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class ProductAttribute(BaseModel):
    """e.g. Color, Size, Material"""
    corporate_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=100)
    display_type = models.CharField(
        max_length=20,
        choices=[("radio", "Radio"), ("color", "Color Swatch"), ("select", "Select")],
        default="radio",
    )
    sequence = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["sequence"]
        unique_together = [("corporate_id", "name")]

    def __str__(self):
        return self.name


class AttributeValue(BaseModel):
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name="values")
    name = models.CharField(max_length=100)
    color_code = models.CharField(max_length=10, blank=True)
    sequence = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["sequence"]
        unique_together = [("attribute", "name")]

    def __str__(self):
        return f"{self.attribute.name}: {self.name}"


class Product(BaseModel):
    PRODUCT_TYPES = [
        ("storable", "Storable Product"),
        ("consumable", "Consumable"),
        ("service", "Service"),
    ]
    COSTING_METHODS = [
        ("fifo", "First In First Out (FIFO)"),
        ("avco", "Average Cost (AVCO)"),
        ("standard", "Standard Price"),
    ]

    corporate_id = models.UUIDField(db_index=True)
    internal_reference = models.CharField(max_length=100, blank=True, db_index=True)
    name = models.CharField(max_length=300, db_index=True)
    description = models.TextField(blank=True)
    description_purchase = models.TextField(blank=True)
    description_sale = models.TextField(blank=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default="storable")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name="products")
    uom_purchase = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT, related_name="purchase_products", null=True, blank=True
    )
    costing_method = models.CharField(max_length=20, choices=COSTING_METHODS, default="avco")
    standard_price = models.DecimalField(max_digits=18, decimal_places=4, default=0, validators=[MinValueValidator(0)])
    list_price = models.DecimalField(max_digits=18, decimal_places=4, default=0, validators=[MinValueValidator(0)])
    taxes_included = models.BooleanField(default=False)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    volume = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    hs_code = models.CharField(max_length=20, blank=True, help_text="Harmonized System code for customs")
    attributes = models.ManyToManyField(ProductAttribute, through="ProductAttributeLine", blank=True)
    is_active = models.BooleanField(default=True)
    can_be_sold = models.BooleanField(default=True)
    can_be_purchased = models.BooleanField(default=True)
    track_lots = models.BooleanField(default=False, help_text="Track by lot/batch")
    track_serials = models.BooleanField(default=False, help_text="Track by serial number")
    expiry_tracking = models.BooleanField(default=False)
    shelf_life_days = models.PositiveIntegerField(null=True, blank=True)
    min_qty = models.DecimalField(max_digits=14, decimal_places=4, default=0, help_text="Minimum stock level")
    reorder_qty = models.DecimalField(max_digits=14, decimal_places=4, default=0, help_text="Qty to reorder when min is reached")
    created_by = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductAttributeLine(BaseModel):
    """Links which attributes (and which values) apply to a product."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attribute_lines")
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    values = models.ManyToManyField(AttributeValue)

    class Meta:
        unique_together = [("product", "attribute")]


class ProductVariant(BaseModel):
    """
    A specific purchasable/sellable variant of a product.
    e.g. 'T-Shirt Red XL' is a variant of 'T-Shirt'.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    combination = models.ManyToManyField(AttributeValue, blank=True)
    sku = models.CharField(max_length=150, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    internal_reference = models.CharField(max_length=100, blank=True)
    standard_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    list_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    volume = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    image = models.ImageField(upload_to="variants/", null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("product", "sku")]

    def __str__(self):
        attrs = ", ".join(str(v) for v in self.combination.all())
        return f"{self.product.name} [{attrs}]" if attrs else self.product.name

    def get_price(self):
        return self.list_price if self.list_price is not None else self.product.list_price

    def get_cost(self):
        return self.standard_price if self.standard_price is not None else self.product.standard_price


class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sequence = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["sequence"]


class PriceList(BaseModel):
    CURRENCY_CHOICES = [("KES", "Kenyan Shilling"), ("USD", "US Dollar"), ("EUR", "Euro"), ("GBP", "British Pound")]

    corporate_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=200)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="KES")
    is_default = models.BooleanField(default=False)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.currency})"


class PriceListItem(BaseModel):
    COMPUTE_METHODS = [
        ("fixed", "Fixed Price"),
        ("discount", "Discount on List Price"),
        ("formula", "Price Formula"),
    ]

    pricelist = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    compute_method = models.CharField(max_length=20, choices=COMPUTE_METHODS, default="fixed")
    fixed_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    min_qty = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["min_qty"]
