from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from .models import (
    AttributeValue,
    Category,
    PriceList,
    PriceListItem,
    Product,
    ProductAttribute,
    ProductAttributeLine,
    ProductImage,
    ProductVariant,
    UnitOfMeasure,
    UnitOfMeasureCategory,
)

admin.site.register(Category, MPTTModelAdmin)
admin.site.register(UnitOfMeasureCategory)
admin.site.register(UnitOfMeasure)
admin.site.register(ProductAttribute)
admin.site.register(AttributeValue)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "internal_reference", "product_type", "standard_price", "list_price", "is_active"]
    list_filter = ["product_type", "is_active", "costing_method"]
    search_fields = ["name", "barcode", "internal_reference"]
    inlines = [ProductVariantInline, ProductImageInline]


admin.site.register(PriceList)
admin.site.register(PriceListItem)
