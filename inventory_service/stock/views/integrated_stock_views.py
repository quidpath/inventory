"""
Integrated Stock Movement Views
Full CRUD operations with automatic synchronization to all services
"""
import logging
from decimal import Decimal
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from inventory_service.stock.models import StockMove, StockLevel, StockLot
from inventory_service.products.models import Product
from inventory_service.warehouse.models import StorageLocation
from inventory_service.services.unified_integration_client import UnifiedIntegrationClient

logger = logging.getLogger(__name__)


@api_view(['POST'])
@transaction.atomic
def create_stock_move_integrated(request):
    """
    Create stock move and sync to all services
    
    POST /api/stock/moves/integrated/
    
    Body:
    {
        "reference": "PO-001",
        "move_type": "receipt",
        "product_id": "uuid",
        "variant_id": "uuid",
        "quantity": "100.00",
        "uom_id": "uuid",
        "unit_cost": "50.00",
        "location_from_id": "uuid",
        "location_to_id": "uuid",
        "lot_id": "uuid",
        "notes": "Initial stock",
        "project_id": "uuid",
        "is_asset": false
    }
    """
    try:
        corporate_id = request.headers.get('X-Corporate-ID')
        user_id = request.headers.get('X-User-ID')
        
        if not corporate_id:
            return Response(
                {'error': 'X-Corporate-ID header is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate required fields
        required_fields = ['move_type', 'product_id', 'quantity', 'uom_id']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get product
        product = get_object_or_404(
            Product,
            id=request.data['product_id'],
            corporate_id=corporate_id
        )
        
        # Create stock move
        move_data = {
            'corporate_id': corporate_id,
            'reference': request.data.get('reference', ''),
            'move_type': request.data['move_type'],
            'product_id': product.id,
            'variant_id': request.data.get('variant_id'),
            'quantity': Decimal(str(request.data['quantity'])),
            'uom_id': request.data['uom_id'],
            'unit_cost': Decimal(str(request.data.get('unit_cost', 0))),
            'location_from_id': request.data.get('location_from_id'),
            'location_to_id': request.data.get('location_to_id'),
            'lot_id': request.data.get('lot_id'),
            'notes': request.data.get('notes', ''),
            'created_by': user_id,
            'state': 'draft',
        }
        
        stock_move = StockMove.objects.create(**move_data)
        
        # Confirm and validate the move
        stock_move.state = 'confirmed'
        stock_move.save()
        stock_move.validate()
        
        # Prepare data for integration
        integration_data = {
            'id': stock_move.id,
            'move_type': stock_move.move_type,
            'product_id': stock_move.product_id,
            'variant_id': stock_move.variant_id,
            'quantity': stock_move.quantity,
            'unit_cost': stock_move.unit_cost,
            'location_from_id': stock_move.location_from_id,
            'location_to_id': stock_move.location_to_id,
            'project_id': request.data.get('project_id'),
            'is_asset': request.data.get('is_asset', False),
        }
        
        # Sync to all services
        integration_client = UnifiedIntegrationClient()
        sync_result = integration_client.sync_stock_move(
            integration_data,
            corporate_id,
            user_id
        )
        
        return Response({
            'success': True,
            'message': 'Stock move created and synced successfully',
            'stock_move': {
                'id': str(stock_move.id),
                'reference': stock_move.reference,
                'move_type': stock_move.move_type,
                'product': product.name,
                'quantity': str(stock_move.quantity),
                'state': stock_move.state,
            },
            'integration': {
                'synced_services': sync_result['synced_services'],
                'accounting_entry_created': sync_result['accounting_entry_created'],
                'errors': sync_result['errors']
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating stock move: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_stock_move(request, move_id):
    """
    Get stock move details
    
    GET /api/stock/moves/integrated/{move_id}/
    """
    try:
        corporate_id = request.headers.get('X-Corporate-ID')
        
        stock_move = get_object_or_404(
            StockMove,
            id=move_id,
            corporate_id=corporate_id
        )
        
        return Response({
            'success': True,
            'stock_move': {
                'id': str(stock_move.id),
                'reference': stock_move.reference,
                'move_type': stock_move.move_type,
                'state': stock_move.state,
                'product': {
                    'id': str(stock_move.product.id),
                    'name': stock_move.product.name,
                },
                'quantity': str(stock_move.quantity),
                'unit_cost': str(stock_move.unit_cost),
                'location_from': stock_move.location_from.name if stock_move.location_from else None,
                'location_to': stock_move.location_to.name if stock_move.location_to else None,
                'done_date': stock_move.done_date.isoformat() if stock_move.done_date else None,
                'notes': stock_move.notes,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting stock move: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def list_stock_moves(request):
    """
    List stock moves with filters
    
    GET /api/stock/moves/integrated/?move_type=receipt&state=done&product_id=uuid
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
        move_type = request.GET.get('move_type', '')
        state = request.GET.get('state', '')
        product_id = request.GET.get('product_id', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        
        # Build query
        moves = StockMove.objects.filter(corporate_id=corporate_id)
        
        if move_type:
            moves = moves.filter(move_type=move_type)
        
        if state:
            moves = moves.filter(state=state)
        
        if product_id:
            moves = moves.filter(product_id=product_id)
        
        if date_from:
            moves = moves.filter(created_at__gte=date_from)
        
        if date_to:
            moves = moves.filter(created_at__lte=date_to)
        
        # Pagination
        total = moves.count()
        start = (page - 1) * page_size
        end = start + page_size
        moves = moves[start:end]
        
        moves_data = [
            {
                'id': str(move.id),
                'reference': move.reference,
                'move_type': move.move_type,
                'state': move.state,
                'product': move.product.name,
                'quantity': str(move.quantity),
                'unit_cost': str(move.unit_cost),
                'created_at': move.created_at.isoformat(),
            }
            for move in moves
        ]
        
        return Response({
            'success': True,
            'total': total,
            'page': page,
            'page_size': page_size,
            'moves': moves_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing stock moves: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_stock_levels(request):
    """
    Get current stock levels
    
    GET /api/stock/levels/?product_id=uuid&location_id=uuid
    """
    try:
        corporate_id = request.headers.get('X-Corporate-ID')
        
        product_id = request.GET.get('product_id', '')
        location_id = request.GET.get('location_id', '')
        
        # Build query
        levels = StockLevel.objects.filter(corporate_id=corporate_id)
        
        if product_id:
            levels = levels.filter(product_id=product_id)
        
        if location_id:
            levels = levels.filter(location_id=location_id)
        
        # Only show levels with quantity > 0
        levels = levels.filter(quantity__gt=0)
        
        levels_data = [
            {
                'product': {
                    'id': str(level.product.id),
                    'name': level.product.name,
                },
                'location': {
                    'id': str(level.location.id),
                    'name': level.location.name,
                },
                'quantity': str(level.quantity),
                'reserved_quantity': str(level.reserved_quantity),
                'available_quantity': str(level.available_quantity),
            }
            for level in levels
        ]
        
        return Response({
            'success': True,
            'total': len(levels_data),
            'stock_levels': levels_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting stock levels: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def check_availability(request):
    """
    Check if product is available in sufficient quantity
    
    POST /api/stock/check-availability/
    
    Body:
    {
        "product_id": "uuid",
        "variant_id": "uuid",
        "quantity": "10.00",
        "location_id": "uuid"
    }
    """
    try:
        corporate_id = request.headers.get('X-Corporate-ID')
        
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')
        quantity = Decimal(str(request.data.get('quantity', 0)))
        location_id = request.data.get('location_id')
        
        if not product_id or not location_id:
            return Response(
                {'error': 'product_id and location_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get stock level
        try:
            stock_level = StockLevel.objects.get(
                corporate_id=corporate_id,
                product_id=product_id,
                variant_id=variant_id,
                location_id=location_id
            )
            
            available = stock_level.available_quantity
            is_available = available >= quantity
            
        except StockLevel.DoesNotExist:
            available = Decimal('0')
            is_available = False
        
        return Response({
            'success': True,
            'available': is_available,
            'available_quantity': str(available),
            'requested_quantity': str(quantity),
            'shortage': str(max(Decimal('0'), quantity - available))
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@transaction.atomic
def adjust_stock(request):
    """
    Adjust stock quantity (increase or decrease)
    
    POST /api/stock/adjust/
    
    Body:
    {
        "product_id": "uuid",
        "variant_id": "uuid",
        "location_id": "uuid",
        "quantity": "10.00",  # positive for increase, negative for decrease
        "reason": "Physical count adjustment",
        "unit_cost": "50.00"
    }
    """
    try:
        corporate_id = request.headers.get('X-Corporate-ID')
        user_id = request.headers.get('X-User-ID')
        
        product_id = request.data.get('product_id')
        location_id = request.data.get('location_id')
        quantity = Decimal(str(request.data.get('quantity', 0)))
        
        if not product_id or not location_id or quantity == 0:
            return Response(
                {'error': 'product_id, location_id, and non-zero quantity are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get product
        product = get_object_or_404(Product, id=product_id, corporate_id=corporate_id)
        
        # Create adjustment move
        move_data = {
            'corporate_id': corporate_id,
            'reference': f'ADJ-{timezone.now().strftime("%Y%m%d%H%M%S")}',
            'move_type': 'adjustment',
            'product_id': product.id,
            'variant_id': request.data.get('variant_id'),
            'quantity': abs(quantity),
            'uom_id': product.uom_id,
            'unit_cost': Decimal(str(request.data.get('unit_cost', product.standard_price))),
            'location_to_id': location_id if quantity > 0 else None,
            'location_from_id': location_id if quantity < 0 else None,
            'notes': request.data.get('reason', 'Stock adjustment'),
            'created_by': user_id,
            'state': 'confirmed',
        }
        
        stock_move = StockMove.objects.create(**move_data)
        stock_move.validate()
        
        # Sync to services
        integration_client = UnifiedIntegrationClient()
        integration_data = {
            'id': stock_move.id,
            'move_type': 'adjustment',
            'product_id': product.id,
            'quantity': quantity,
            'unit_cost': stock_move.unit_cost,
            'location_to_id': location_id,
        }
        
        sync_result = integration_client.sync_stock_move(
            integration_data,
            corporate_id,
            user_id
        )
        
        return Response({
            'success': True,
            'message': 'Stock adjusted successfully',
            'adjustment': {
                'reference': stock_move.reference,
                'product': product.name,
                'quantity_change': str(quantity),
                'new_quantity': str(StockLevel.objects.get(
                    corporate_id=corporate_id,
                    product_id=product_id,
                    location_id=location_id
                ).quantity)
            },
            'integration': {
                'synced_services': sync_result['synced_services'],
                'accounting_entry_created': sync_result['accounting_entry_created']
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error adjusting stock: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
