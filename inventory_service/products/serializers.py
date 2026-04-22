"""
Product Serializers for Inventory Service
"""
from rest_framework import serializers

from .models import (
    Product, ProductVariant, Category, UnitOfMeasure, UnitOfMeasureCategory,
    ProductAttribute, AttributeValue, ProductAttributeLine, ProductImage,
    PriceList, PriceListItem
)


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'corporate_id', 'name', 'slug', 'parent', 'parent_name',
            'description', 'image', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UnitOfMeasureCategorySerializer(serializers.ModelSerializer):
    """Serializer for UoM categories"""
    
    class Meta:
        model = UnitOfMeasureCategory
        fields = ['id', 'corporate_id', 'name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    """Serializer for units of measure"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = UnitOfMeasure
        fields = [
            'id', 'corporate_id', 'category', 'category_name', 'name', 'symbol',
            'factor', 'rounding', 'is_base', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Ensure required fields are present"""
        if not data.get('name'):
            raise serializers.ValidationError({'name': 'This field is required.'})
        if not data.get('symbol'):
            raise serializers.ValidationError({'symbol': 'This field is required.'})
        return data


class AttributeValueSerializer(serializers.ModelSerializer):
    """Serializer for attribute values"""
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    
    class Meta:
        model = AttributeValue
        fields = [
            'id', 'attribute', 'attribute_name', 'name', 'color_code',
            'sequence', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductAttributeSerializer(serializers.ModelSerializer):
    """Serializer for product attributes"""
    values = AttributeValueSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductAttribute
        fields = [
            'id', 'corporate_id', 'name', 'display_type', 'sequence',
            'values', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images"""
    
    class Meta:
        model = ProductImage
        fields = [
            'id', 'product', 'image', 'alt_text', 'is_primary',
            'sequence', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for product variants"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    combination_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'product_name', 'combination', 'combination_display',
            'sku', 'barcode', 'internal_reference', 'standard_price', 'list_price',
            'weight', 'volume', 'image', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_combination_display(self, obj):
        """Get human-readable combination of attributes"""
        return ', '.join(str(v) for v in obj.combination.all())


class ProductSerializer(serializers.ModelSerializer):
    """Main product serializer with all related data"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    uom_name = serializers.CharField(source='uom.name', read_only=True)
    uom_symbol = serializers.CharField(source='uom.symbol', read_only=True)
    uom_purchase_name = serializers.CharField(source='uom_purchase.name', read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'corporate_id', 'internal_reference', 'name', 'description',
            'description_purchase', 'description_sale', 'product_type',
            'category', 'category_name', 'uom', 'uom_name', 'uom_symbol',
            'uom_purchase', 'uom_purchase_name', 'costing_method',
            'standard_price', 'list_price', 'taxes_included', 'tax_rate',
            'weight', 'volume', 'barcode', 'hs_code', 'is_active',
            'can_be_sold', 'can_be_purchased', 'track_lots', 'track_serials',
            'expiry_tracking', 'shelf_life_days', 'min_qty', 'reorder_qty',
            'created_by', 'created_at', 'updated_at', 'variants', 'images'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'uom': {'required': False},  # Make uom not required so we can handle uom_id
            'category': {'required': False}  # Make category not required so we can handle category_id
        }
    
    def to_internal_value(self, data):
        """
        Convert incoming data to internal representation.
        Handle uom_id -> uom and category_id -> category conversion.
        """
        # If uom_id is provided but not uom, map it
        if 'uom_id' in data and 'uom' not in data:
            data['uom'] = data.pop('uom_id')
        
        # If category_id is provided but not category, map it
        if 'category_id' in data and 'category' not in data:
            data['category'] = data.pop('category_id')
        
        return super().to_internal_value(data)


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    uom_symbol = serializers.CharField(source='uom.symbol', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'internal_reference', 'name', 'product_type',
            'category_name', 'uom_symbol', 'standard_price', 'list_price',
            'barcode', 'is_active', 'can_be_sold', 'can_be_purchased'
        ]
        read_only_fields = ['id']


class PriceListSerializer(serializers.ModelSerializer):
    """Serializer for price lists"""
    
    class Meta:
        model = PriceList
        fields = [
            'id', 'corporate_id', 'name', 'currency', 'is_default',
            'date_start', 'date_end', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PriceListItemSerializer(serializers.ModelSerializer):
    """Serializer for price list items"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_sku = serializers.CharField(source='variant.sku', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = PriceListItem
        fields = [
            'id', 'pricelist', 'product', 'product_name', 'variant', 'variant_sku',
            'category', 'category_name', 'compute_method', 'fixed_price',
            'discount_percent', 'min_qty', 'date_start', 'date_end',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
