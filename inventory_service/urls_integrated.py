"""
Integrated URLs for Inventory Service
Routes for full CRUD operations with cross-service synchronization
"""
from django.urls import path

from inventory_service.products.views.integrated_product_views import (
    create_product_integrated,
    get_product_integrated,
    update_product_integrated,
    delete_product_integrated,
    list_products_integrated,
    bulk_sync_products,
    check_integration_health,
)

from inventory_service.stock.views.integrated_stock_views import (
    create_stock_move_integrated,
    get_stock_move,
    list_stock_moves,
    get_stock_levels,
    check_availability,
    adjust_stock,
)

urlpatterns = [
    # ==================== PRODUCT CRUD ====================
    # Create
    path('products/integrated/', create_product_integrated, name='create_product_integrated'),
    
    # Read
    path('products/integrated/<uuid:product_id>/', get_product_integrated, name='get_product_integrated'),
    path('products/integrated/list/', list_products_integrated, name='list_products_integrated'),
    
    # Update
    path('products/integrated/<uuid:product_id>/update/', update_product_integrated, name='update_product_integrated'),
    
    # Delete
    path('products/integrated/<uuid:product_id>/delete/', delete_product_integrated, name='delete_product_integrated'),
    
    # Bulk operations
    path('products/integrated/bulk-sync/', bulk_sync_products, name='bulk_sync_products'),
    
    # Health check
    path('products/integrated/health/', check_integration_health, name='check_integration_health'),
    
    # ==================== STOCK MOVEMENT CRUD ====================
    # Create
    path('stock/moves/integrated/', create_stock_move_integrated, name='create_stock_move_integrated'),
    
    # Read
    path('stock/moves/integrated/<uuid:move_id>/', get_stock_move, name='get_stock_move'),
    path('stock/moves/integrated/list/', list_stock_moves, name='list_stock_moves'),
    
    # Stock levels
    path('stock/levels/', get_stock_levels, name='get_stock_levels'),
    path('stock/check-availability/', check_availability, name='check_availability'),
    
    # Stock adjustments
    path('stock/adjust/', adjust_stock, name='adjust_stock'),
]
