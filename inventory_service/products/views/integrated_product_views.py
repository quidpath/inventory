"""
Integrated Product Views
Full CRUD operations with automatic synchronization to all services
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction

from inventory_service.products.models import Product, ProductVariant
from inventory_service.products.serializers import ProductSerializer, ProductVariantSerializer
from inventory_service.services.unified_integration_client import UnifiedIntegrationClient

logger = logging.getLogger(__name__)


@api_view(['POST'])
@transaction.atomic
def create_product_integrated(request):
    """
    Create product and sync to all services
    
    POST /api/products/integrated/
    
    Body:
    {
        "name": "Product Name",
        "internal_reference": "SKU-001",
        "description": "Product description",
        "product_type": "storable",
        "category_id": "uuid",
        "uom_id": "uuid",
        "standard_price": "100.00",
        "list_price": "150.00",
        "costing_method": "avco",
        "can_be_sold": true,
        "can_be_purchased": true,
        "track_lots": false,
        "track_serials": false,
        "min_qty": "10.00",
        "reorder_qty": "50.00"
    }
    """
    try:
        # Get headers
        corporate_id = request.headers.get('X-Corporate-ID')
        user_id = request.headers.get('X-User-ID')
        
        if not corporate_id:
            return Response(
                {'error': 'X-Corporate-ID header is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add corporate_id to data
        data = request.data.copy()
        data['corporate_id'] = corporate_id
        data['created_by'] = user_id
        
        # Create product
        serializer = ProductSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid product data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product = serializer.save()
        
        # Sync to all services
        integration_client = UnifiedIntegrationClient()
        
        product_data = {
            'id': product.id,
            'name': product.name,
            'internal_reference': product.internal_reference,
            'description': product.description,
            'product_type': product.product_type,
            'standard_price': product.standard_price,
            'list_price': product.list_price,
            'costing_method': product.costing_method,
            'can_be_sold': product.can_be_sold,
            'can_be_purchased': product.can_be_purchased,
            'barcode': product.barcode,
            'tax_rate': product.tax_rate,
            'is_active': product.is_active,
            'category_name': product.category.name if product.category else '',
            'uom_name': product.uom.name if product.uom else '',
        }
        
        sync_result = integration_client.create_product(
            product_data,
            corporate_id,
            user_id
        )
        
        return Response({
            'success': True,
            'message': 'Product created successfully',
            'product': ProductSerializer(product).data,
            'integration': {
                'synced_services': sync_result['synced_services'],
                'errors': sync_result['errors']
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_product_integrated(request, product_id):
    """
    Get product with integration status
    
    GET /api/products/integrated/{product_id}/
    """
    try:
        corporate_id = request.headers.get('X-Corporate-ID')
        
        product = get_object_or_404(
            Product,
            id=product_id,
            corporate_id=corporate_id
        )
        
        # Get integration status
        integration_client = UnifiedIntegrationClient()
        connectivity = integration_client.check_service_connectivity(corporate_id)
        
        return Response({
            'success': True,
            'product': ProductSerializer(product).data,
            'integration_status': connectivity
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting product: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@transaction.atomic
def update_product_integrated(request, product_id):
    """
    Update product and sync to all services
    
    PUT/PATCH /api/products/integrated/{product_id}/
    """
    try:
        corporate_id = request.headers.get('X-Corporate-ID')
        user_id = request.headers.get('X-User-ID')
        
        product = get_object_or_404(
            Product,
            id=product_id,
            corporate_id=corporate_id
        )
        
        # Update product
        partial = request.method == 'PATCH'
        serializer = ProductSerializer(product, data=request.data, partial=partial)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid product data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product = serializer.save()
        
        # Sync to all services
        integration_client = UnifiedIntegrationClient()
        
        product_data = {
            'id': product.id,
            'name': product.name,
            'internal_reference': product.internal_reference,
            'description': product.description,
            'product_type': product.product_type,
            'standard_price': product.standard_price,
            'list_price': product.list_price,
            'costing_method': product.costing_method,
            'can_be_sold': product.can_be_sold,
            'can_be_purchased': product.can_be_purchased,
            'barcode': product.barcode,
            'tax_rate': product.tax_rate,
            'is_active': product.is_active,
            'category_name': product.category.name if product.category else '',
            'uom_name': product.uom.name if product.uom else '',
        }
        
        sync_result = integration_client.update_product(
            product_data,
            corporate_id,
            user_id
        )
        
        return Response({
            'success': True,
            'message': 'Product updated successfully',
            'product': ProductSerializer(product).data,
            'integration': {
                'synced_services': sync_result['synced_services'],
                'errors': sync_result['errors']
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@transaction.atomic
def delete_product_integrated(request, product_id):
    """
    Delete product and remove from all services
    
    DELETE /api/products/integrated/{product_id}/
    """
    try:
        corporate_id = request.headers.get('X-Corporate-ID')
        user_id = request.headers.get('X-User-ID')
        
        product = get_object_or_404(
            Product,
            id=product_id,
            corporate_id=corporate_id
        )
        
        # Check if product has stock
        if product.stock_levels.filter(quantity__gt=0).exists():
            return Response(
                {'error': 'Cannot delete product with existing stock'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove from all services first
        integration_client = UnifiedIntegrationClient()
        sync_result = integration_client.delete_product(
            product_id,
            corporate_id,
            user_id
        )
        
        # Delete product
        product_name = product.name
        product.delete()
        
        return Response({
            'success': True,
            'message': f'Product "{product_name}" deleted successfully',
            'integration': {
                'removed_from': sync_result['removed_from'],
                'errors': sync_result['errors']
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def list_products_integrated(request):
    """
    List all products with pagination
    
    GET /api/products/integrated/?page=1&page_size=50&search=query
    """
    try:
        # Handle both service-to-service calls and user calls
        if hasattr(request, 'service_call') and request.service_call:
            # Service-to-service call - get from query params
            corporate_id = request.GET.get('corporate_id')
        else:
            # User call - get from headers
            corporate_id = request.headers.get('X-Corporate-ID')
        
        if not corporate_id:
            return Response(
                {'error': 'corporate_id is required (header X-Corporate-ID or query param)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        search = request.GET.get('search', '')
        product_type = request.GET.get('product_type', '')
        is_active = request.GET.get('is_active', '')
        
        # Build query
        products = Product.objects.filter(corporate_id=corporate_id)
        
        if search:
            products = products.filter(
                name__icontains=search
            ) | products.filter(
                internal_reference__icontains=search
            ) | products.filter(
                barcode__icontains=search
            )
        
        if product_type:
            products = products.filter(product_type=product_type)
        
        if is_active:
            products = products.filter(is_active=is_active.lower() == 'true')
        
        # Pagination
        total = products.count()
        start = (page - 1) * page_size
        end = start + page_size
        products = products[start:end]
        
        return Response({
            'success': True,
            'total': total,
            'page': page,
            'page_size': page_size,
            'products': ProductSerializer(products, many=True).data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing products: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def bulk_sync_products(request):
    """
    Bulk sync products to all services
    
    POST /api/products/integrated/bulk-sync/
    
    Body:
    {
        "product_ids": ["uuid1", "uuid2", "uuid3"]
    }
    """
    try:
        corporate_id = request.headers.get('X-Corporate-ID')
        user_id = request.headers.get('X-User-ID')
        
        product_ids = request.data.get('product_ids', [])
        
        if not product_ids:
            return Response(
                {'error': 'product_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        integration_client = UnifiedIntegrationClient()
        result = integration_client.bulk_sync_products(
            product_ids,
            corporate_id,
            user_id
        )
        
        return Response({
            'success': True,
            'message': f'Synced {result["success"]} products',
            'details': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error bulk syncing products: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def check_integration_health(request):
    """
    Check health of all integrated services
    
    GET /api/products/integrated/health/
    """
    try:
        # Handle both service-to-service calls and user calls
        if hasattr(request, 'service_call') and request.service_call:
            # Service-to-service call - use default corporate_id or get from query params
            corporate_id = request.GET.get('corporate_id')
        else:
            # User call - get from headers
            corporate_id = request.headers.get('X-Corporate-ID')
        
        integration_client = UnifiedIntegrationClient()
        connectivity = integration_client.check_service_connectivity(corporate_id)
        
        all_online = all(
            service['status'] == 'online' 
            for service in connectivity.values()
        )
        
        return Response({
            'success': True,
            'all_services_online': all_online,
            'services': connectivity
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking integration health: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
