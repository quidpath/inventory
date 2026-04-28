"""
Warehouse Serializers for Inventory Service
"""
from rest_framework import serializers
from .models import Warehouse, StorageLocation


class StorageLocationSerializer(serializers.ModelSerializer):
    """Serializer for storage locations"""
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = StorageLocation
        fields = [
            'id', 'warehouse', 'warehouse_name', 'parent', 'parent_name',
            'name', 'complete_name', 'location_type', 'barcode', 'is_active',
            'posx', 'posy', 'posz', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'complete_name']


class WarehouseSerializer(serializers.ModelSerializer):
    """Serializer for warehouses"""
    locations = StorageLocationSerializer(many=True, read_only=True)
    location_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Warehouse
        fields = [
            'id', 'corporate_id', 'name', 'short_name', 'address_line1',
            'address_line2', 'city', 'country', 'phone', 'email',
            'is_active', 'locations', 'location_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_location_count(self, obj):
        """Get count of active locations"""
        return obj.locations.filter(is_active=True).count()
    
    def validate(self, data):
        """Ensure required fields are present"""
        if not data.get('name'):
            raise serializers.ValidationError({'name': 'This field is required.'})
        if not data.get('short_name'):
            raise serializers.ValidationError({'short_name': 'This field is required.'})
        return data


class WarehouseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for warehouse lists"""
    location_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Warehouse
        fields = [
            'id', 'name', 'short_name', 'city', 'country',
            'is_active', 'location_count'
        ]
        read_only_fields = ['id']
    
    def get_location_count(self, obj):
        """Get count of active locations"""
        return obj.locations.filter(is_active=True).count()
