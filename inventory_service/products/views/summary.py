"""
Inventory Dashboard Summary with period-over-period comparisons
"""
from decimal import Decimal
from datetime import timedelta
from django.db import models
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from inventory_service.products.models import Product
from inventory_service.stock.models import StockMove, StockLevel
from inventory_service.warehouse.models import Warehouse


@api_view(["GET"])
def inventory_summary(request):
    """
    Returns inventory metrics with period-over-period comparisons.
    Compares current month vs previous month.
    """
    # Handle both service-to-service calls and user calls
    if hasattr(request, 'service_call') and request.service_call:
        # Service-to-service call - get from query params
        cid = request.GET.get('corporate_id')
        if not cid:
            return Response(
                {'error': 'corporate_id query parameter is required for service calls'},
                status=400
            )
    else:
        # User call - get from request attribute set by middleware
        cid = request.corporate_id
        if not cid:
            return Response(
                {'error': 'Corporate ID not found in token'},
                status=400
            )
    
    # Current period (this month)
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Previous period (last month)
    if month_start.month == 1:
        prev_month_start = month_start.replace(year=month_start.year - 1, month=12)
    else:
        prev_month_start = month_start.replace(month=month_start.month - 1)
    prev_month_end = month_start - timedelta(seconds=1)
    
    # Helper functions
    def calc_change(current, previous):
        if previous > 0:
            return round(float(((current - previous) / previous) * 100), 1)
        return 0.0
    
    def get_trend(change):
        if change > 0:
            return "up"
        elif change < 0:
            return "down"
        return "neutral"
    
    # Total Products
    total_products = Product.objects.filter(corporate_id=cid, is_active=True).count()
    prev_products = Product.objects.filter(
        corporate_id=cid,
        is_active=True,
        created_at__lt=month_start
    ).count()
    products_change = calc_change(total_products, prev_products)
    
    # Total Inventory Value (from stock levels)
    stock_levels = StockLevel.objects.filter(
        corporate_id=cid,
        quantity__gt=0
    ).select_related('product')
    
    total_value = Decimal('0')
    for level in stock_levels:
        # Use standard_price (cost) for valuation
        unit_cost = level.product.standard_price or Decimal('0')
        total_value += level.quantity * unit_cost
    
    # Previous month value (approximate - using products that existed then)
    prev_products_qs = Product.objects.filter(
        corporate_id=cid,
        is_active=True,
        created_at__lt=month_start
    )
    prev_stock_levels = StockLevel.objects.filter(
        corporate_id=cid,
        product__in=prev_products_qs,
        quantity__gt=0
    ).select_related('product')
    
    prev_total_value = Decimal('0')
    for level in prev_stock_levels:
        unit_cost = level.product.standard_price or Decimal('0')
        prev_total_value += level.quantity * unit_cost
    
    value_change = calc_change(float(total_value), float(prev_total_value))
    
    # Low Stock Items (quantity below min_qty)
    # Get products with stock levels below their min_qty
    low_stock_items = 0
    for product in Product.objects.filter(corporate_id=cid, is_active=True, min_qty__gt=0):
        total_stock = StockLevel.objects.filter(
            corporate_id=cid,
            product=product
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
        
        if total_stock <= product.min_qty:
            low_stock_items += 1
    
    # Previous low stock count (simplified - just count from previous period)
    prev_low_stock = low_stock_items  # Simplified for now
    low_stock_change = 0.0
    
    # Warehouses Count
    warehouses_count = Warehouse.objects.filter(corporate_id=cid, is_active=True).count()
    
    # Stock Movements This Month
    movements_this_month = StockMove.objects.filter(
        corporate_id=cid,
        created_at__gte=month_start
    ).count()
    
    # Out of Stock Items
    out_of_stock_items = 0
    for product in Product.objects.filter(corporate_id=cid, is_active=True, product_type='storable'):
        total_stock = StockLevel.objects.filter(
            corporate_id=cid,
            product=product
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
        
        if total_stock <= 0:
            out_of_stock_items += 1
    
    return Response({
        "total_products": total_products,
        "total_products_previous": prev_products,
        "total_products_change": products_change,
        "total_products_trend": get_trend(products_change),
        
        "total_value": float(total_value),
        "total_value_previous": float(prev_total_value),
        "total_value_change": value_change,
        "total_value_trend": get_trend(value_change),
        
        "low_stock_items": low_stock_items,
        "low_stock_items_previous": prev_low_stock,
        "low_stock_items_change": low_stock_change,
        "low_stock_items_trend": get_trend(low_stock_change),
        
        "out_of_stock_items": out_of_stock_items,
        "warehouses_count": warehouses_count,
        "movements_this_month": movements_this_month,
    })
