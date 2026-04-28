"""
Stock Serializers for Inventory Service
"""
from rest_framework import serializers
from .models import StockMove, StockLevel, StockLot, SerialNumber, ReorderRule


class StockLotSerializer(serializers.ModelSerializer):
    """Serializer for stock lots"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = StockLot
        fields = [
            'id', 'corporate_id', 'product', 'product_name', 'lot_number',
            'expiry_date', 'manufacture_date', 'supplier_lot', 'notes',
            'is_active', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SerialNumberSerializer(serializers.ModelSerializer):
    """Serializer for serial numbers"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    
    class Meta:
        model = SerialNumber
        fields = [
            'id', 'corporate_id', 'product', 'product_name', 'variant',
            'serial_number', 'state', 'location', 'location_name', 'lot',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StockLevelSerializer(serializers.ModelSerializer):
    """Serializer for stock levels"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.internal_reference', read_only=True)
    location_name = serializers.CharField(source='location.complete_name', read_only=True)
    warehouse_name = serializers.CharField(source='location.warehouse.name', read_only=True)
    available_quantity = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)
    
    class Meta:
        model = StockLevel
        fields = [
            'id', 'corporate_id', 'product', 'product_name', 'product_sku',
            'variant', 'location', 'location_name', 'warehouse_name', 'lot',
            'quantity', 'reserved_quantity', 'available_quantity',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StockMoveSerializer(serializers.ModelSerializer):
    """Serializer for stock moves"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.internal_reference', read_only=True)
    location_from_name = serializers.CharField(source='location_from.complete_name', read_only=True)
    location_to_name = serializers.CharField(source='location_to.complete_name', read_only=True)
    uom_symbol = serializers.CharField(source='uom.symbol', read_only=True)
    move_type_display = serializers.CharField(source='get_move_type_display', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    
    class Meta:
        model = StockMove
        fields = [
            'id', 'corporate_id', 'reference', 'move_type', 'move_type_display',
            'state', 'state_display', 'product', 'product_name', 'product_sku',
            'variant', 'lot', 'serial', 'location_from', 'location_from_name',
            'location_to', 'location_to_name', 'quantity', 'uom', 'uom_symbol',
            'unit_cost', 'scheduled_date', 'done_date', 'notes', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReorderRuleSerializer(serializers.ModelSerializer):
    """Serializer for reorder rules"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    location_name = serializers.CharField(source='location.complete_name', read_only=True)
    
    class Meta:
        model = ReorderRule
        fields = [
            'id', 'corporate_id', 'product', 'product_name', 'variant',
            'location', 'location_name', 'min_qty', 'max_qty', 'reorder_qty',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
