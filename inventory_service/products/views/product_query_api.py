"""
Product Query API for Service-to-Service Integration
Other services query these endpoints to get product information
"""
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Sum, F
from django.shortcuts import get_object_or_404

from inventory_service.products.models import Product, ProductVariant
from inventory_service.stock.models import StockMove, StockQuant

logger = logging.getLogger(__name__)


@api_view(['GET'])
def get_product_details(request, product_id):
    """
    Get detailed product information
    
    GET /api/inventory/products/{product_id}/
    
    Used by: POS, Projects, CRM, HRM
    """
    try:
        corporate_id = request.corporate_id
        
        product = get_object_or_404(
            Product,
            id=product_id,
            corporate_id=corporate_id
        )
        
        # Get current stock level
        stock_quants = StockQuant.objects.filter(
            product=product,
            corporate_id=corporate_id
        ).aggregate(
            total_quantity=Sum('quantity')
        )
        
        available_stock = stock_quants['total_quantity'] or 0
        
        data = {
            'id': str(product.id),
            'name': product.name,
            'internal_reference': product.internal_reference or '',
            'barcode': product.barcode or '',
            'description': product.description or '',
            'list_price': str(product.list_price),
            'standard_price': str(product.standard_price),
            'product_type': product.product_type,
            'can_be_sold': product.can_be_sold,
            'can_be_purchased': product.can_be_purchased,
            'category_id': product.category_id,
            'category_name': product.category.name if product.category else '',
            'uom_id': product.uom_id,
            'uom_name': product.uom.name if product.uom else 'Unit',
            'tax_rate': str(product.tax_rate) if hasattr(product, 'tax_rate') else '0.00',
            'available_stock': str(available_stock),
            'is_active': product.is_active,
        }
        
        return Response(data, status=status.HTTP_200_OK)
        
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error getting product details: {str(e)}", exc_info=True)
        return Response(
            {'error': f'Failed to get product: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def get_products_bulk(request):
    """
    Get multiple products at once
    
    POST /api/inventory/products/bulk/
    
    Body: {
        "product_ids": ["uuid1", "uuid2", "uuid3"]
    }
    
    Used by: All services when displaying multiple products
    """
    try:
        corporate_id = request.corporate_id
        product_ids = request.data.get('product_ids', [])
        
        if not product_ids:
            return Response(
                {'error': 'product_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        products = Product.objects.filter(
            id__in=product_ids,
            corporate_id=corporate_id
        ).select_related('category', 'uom')
        
        # Get stock levels for all products
        stock_levels = {}
        stock_quants = StockQuant.objects.filter(
            product__in=products,
            corporate_id=corporate_id
        ).values('product_id').annotate(
            total_quantity=Sum('quantity')
        )
        
        for sq in stock_quants:
            stock_levels[str(sq['product_id'])] = sq['total_quantity'] or 0
        
        data = []
        for product in products:
            data.append({
                'id': str(product.id),
                'name': product.name,
                'internal_reference': product.internal_reference or '',
                'barcode': product.barcode or '',
                'list_price': str(product.list_price),
                'standard_price': str(product.standard_price),
                'product_type': product.product_type,
                'category_name': product.category.name if product.category else '',
                'uom_name': product.uom.name if product.uom else 'Unit',
                'available_stock': str(stock_levels.get(str(product.id), 0)),
                'is_active': product.is_active,
            })
        
        return Response({
            'count': len(data),
            'products': data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting products bulk: {str(e)}", exc_info=True)
        return Response(
            {'error': f'Failed to get products: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def search_products(request):
    """
    Search products by name, SKU, or barcode
    
    GET /api/inventory/products/search/?q=search_term
    
    Used by: POS (barcode scan), CRM (product selection), Projects (material selection)
    """
    try:
        corporate_id = request.corporate_id
        query = request.GET.get('q', '').strip()
        
        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Search by name, SKU, or barcode
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(internal_reference__icontains=query) |
            Q(barcode=query),
            corporate_id=corporate_id,
            is_active=True
        ).select_related('category', 'uom')[:20]  # Limit to 20 results
        
        # Get stock levels
        product_ids = [p.id for p in products]
        stock_levels = {}
        if product_ids:
            stock_quants = StockQuant.objects.filter(
                product_id__in=product_ids,
                corporate_id=corporate_id
            ).values('product_id').annotate(
                total_quantity=Sum('quantity')
            )
            
            for sq in stock_quants:
                stock_levels[str(sq['product_id'])] = sq['total_quantity'] or 0
        
        data = []
        for product in products:
            data.append({
                'id': str(product.id),
                'name': product.name,
                'internal_reference': product.internal_reference or '',
                'barcode': product.barcode or '',
                'list_price': str(product.list_price),
                'standard_price': str(product.standard_price),
                'product_type': product.product_type,
                'category_name': product.category.name if product.category else '',
                'uom_name': product.uom.name if product.uom else 'Unit',
                'available_stock': str(stock_levels.get(str(product.id), 0)),
                'can_be_sold': product.can_be_sold,
            })
        
        return Response({
            'count': len(data),
            'products': data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}", exc_info=True)
        return Response(
            {'error': f'Failed to search products: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_stock_level(request, product_id):
    """
    Get current stock level for a product
    
    GET /api/inventory/products/{product_id}/stock/
    
    Used by: POS (before sale), Projects (before usage)
    """
    try:
        corporate_id = request.corporate_id
        
        product = get_object_or_404(
            Product,
            id=product_id,
            corporate_id=corporate_id
        )
        
        # Get stock by location
        stock_by_location = StockQuant.objects.filter(
            product=product,
            corporate_id=corporate_id
        ).values(
            'location__name'
        ).annotate(
            quantity=Sum('quantity')
        )
        
        # Total available
        total_quantity = sum(item['quantity'] for item in stock_by_location)
        
        data = {
            'product_id': str(product.id),
            'product_name': product.name,
            'total_available': str(total_quantity),
            'by_location': [
                {
                    'location': item['location__name'],
                    'quantity': str(item['quantity'])
                }
                for item in stock_by_location
            ]
        }
        
        return Response(data, status=status.HTTP_200_OK)
        
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error getting stock level: {str(e)}", exc_info=True)
        return Response(
            {'error': f'Failed to get stock level: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def list_products_for_sale(request):
    """
    List all products available for sale
    
    GET /api/inventory/products/for-sale/
    
    Used by: POS (product catalog), CRM (quote products)
    """
    try:
        corporate_id = request.corporate_id
        
        products = Product.objects.filter(
            corporate_id=corporate_id,
            is_active=True,
            can_be_sold=True
        ).select_related('category', 'uom').order_by('name')
        
        # Get stock levels
        product_ids = [p.id for p in products]
        stock_levels = {}
        if product_ids:
            stock_quants = StockQuant.objects.filter(
                product_id__in=product_ids,
                corporate_id=corporate_id
            ).values('product_id').annotate(
                total_quantity=Sum('quantity')
            )
            
            for sq in stock_quants:
                stock_levels[str(sq['product_id'])] = sq['total_quantity'] or 0
        
        data = []
        for product in products:
            data.append({
                'id': str(product.id),
                'name': product.name,
                'internal_reference': product.internal_reference or '',
                'barcode': product.barcode or '',
                'list_price': str(product.list_price),
                'category_name': product.category.name if product.category else '',
                'available_stock': str(stock_levels.get(str(product.id), 0)),
            })
        
        return Response({
            'count': len(data),
            'products': data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing products for sale: {str(e)}", exc_info=True)
        return Response(
            {'error': f'Failed to list products: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
