from django.contrib import admin
from django.urls import include, path

from inventory_service.health_check import health_check, simple_health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("api/inventory/health/", simple_health, name="simple_health"),
    path("api/inventory/products/", include("inventory_service.products.urls")),
    path("api/inventory/warehouse/", include("inventory_service.warehouse.urls")),
    path("api/inventory/stock/", include("inventory_service.stock.urls")),
    path("api/inventory/valuation/", include("inventory_service.valuation.urls")),
    path("api/inventory/counting/", include("inventory_service.counting.urls")),
    # Integrated routes with cross-service synchronization
    path("api/inventory/", include("inventory_service.urls_integrated")),
]
