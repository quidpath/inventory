"""
Simple health check endpoint that doesn't require authentication
"""
from django.http import JsonResponse
from django.db import connection


def health_check(request):
    """
    Simple health check endpoint
    GET /health/
    """
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'service': 'inventory',
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'service': 'inventory',
            'database': 'disconnected',
            'error': str(e)
        }, status=500)


def simple_health(request):
    """
    Ultra-simple health check
    GET /api/inventory/health/
    """
    return JsonResponse({'status': 'ok', 'service': 'inventory'})