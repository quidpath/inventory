from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from inventory_service.core.utils.request_parser import get_clean_data
from inventory_service.core.utils.response import ResponseProvider
from inventory_service.core.utils.log_base import TransactionLogBase
from inventory_service.core.services.registry import ServiceRegistry
from inventory_service.warehouse.serializers import WarehouseSerializer, WarehouseListSerializer, StorageLocationSerializer


@csrf_exempt
@require_http_methods(["GET", "POST"])
def warehouse_list_create(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    if request.method == "GET":
        filter_data = {"corporate_id": corporate_id}
        if (data.get("active_only") or request.GET.get("active_only", "")).lower() == "true":
            filter_data["is_active"] = True
        items = registry.database("warehouse", "filter", data=filter_data)
        # Use serializer for consistent output
        from inventory_service.warehouse.models import Warehouse
        warehouses = Warehouse.objects.filter(corporate_id=corporate_id)
        if (data.get("active_only") or request.GET.get("active_only", "")).lower() == "true":
            warehouses = warehouses.filter(is_active=True)
        serializer = WarehouseListSerializer(warehouses, many=True)
        return ResponseProvider.success_response(data={"results": serializer.data, "count": warehouses.count()}, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    create_data = {k: v for k, v in data.items() if k in ("name", "short_name", "address_line1", "address_line2", "city", "country", "phone", "email", "is_active")}
    create_data["corporate_id"] = corporate_id
    try:
        created = registry.database("warehouse", "create", data=create_data)
        # Automatically create a default storage location for the warehouse
        try:
            default_location_data = {
                "warehouse_id": created["id"],
                "name": "Main Storage",
                "complete_name": "Main Storage",
                "location_type": "internal",
                "is_active": True,
            }
            registry.database("storagelocation", "create", data=default_location_data)
        except Exception as loc_error:
            # Log but don't fail warehouse creation if location creation fails
            import logging
            logging.getLogger(__name__).warning(f"Failed to create default location for warehouse {created['id']}: {loc_error}")
        # Return serialized data
        from inventory_service.warehouse.models import Warehouse
        warehouse = Warehouse.objects.get(id=created["id"])
        serializer = WarehouseSerializer(warehouse)
        return ResponseProvider.success_response(data=serializer.data, message="Created", status=201)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("warehouse_created", user=user_id, message="Warehouse created", state_name="Completed", request=request)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def warehouse_detail(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    from inventory_service.warehouse.models import Warehouse
    try:
        warehouse = Warehouse.objects.get(id=pk, corporate_id=corporate_id)
    except Warehouse.DoesNotExist:
        return ResponseProvider.error_response("Not found", status=404)
    if request.method == "GET":
        serializer = WarehouseSerializer(warehouse)
        return ResponseProvider.success_response(data=serializer.data, status=200)
    if request.method == "DELETE":
        warehouse.is_active = False
        warehouse.save()
        return ResponseProvider.success_response(message="Deactivated", status=200)
    update_data = {k: v for k, v in data.items() if k in ("name", "short_name", "address_line1", "address_line2", "city", "country", "phone", "email", "is_active")}
    if not update_data:
        serializer = WarehouseSerializer(warehouse)
        return ResponseProvider.success_response(data=serializer.data, status=200)
    try:
        for key, value in update_data.items():
            setattr(warehouse, key, value)
        warehouse.save()
        serializer = WarehouseSerializer(warehouse)
        return ResponseProvider.success_response(data=serializer.data, status=200)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def location_list_create(request, warehouse_pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        wh = registry.database("warehouse", "get", data={"id": warehouse_pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Warehouse not found", status=404)
    if request.method == "GET":
        filter_data = {"warehouse_id": warehouse_pk}
        items = registry.database("storagelocation", "filter", data=filter_data)
        if (data.get("flat") or request.GET.get("flat", "false")).lower() == "true":
            return ResponseProvider.success_response(data=items, status=200)
        root = [loc for loc in items if loc.get("parent_id") is None]
        return ResponseProvider.success_response(data=root, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    create_data = {k: v for k, v in data.items() if k in ("parent_id", "name", "complete_name", "location_type", "barcode", "is_active", "posx", "posy", "posz")}
    create_data["warehouse_id"] = warehouse_pk
    try:
        created = registry.database("storagelocation", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("storage_location_created", user=user_id, message="Storage location created", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def location_detail(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    from django.db.models import Q
    items = registry.database("storagelocation", "filter", data=Q(pk=pk) & Q(warehouse__corporate_id=corporate_id))
    loc = items[0] if isinstance(items, list) and items else None
    if not loc:
        return ResponseProvider.error_response("Not found", status=404)
    if request.method == "GET":
        return ResponseProvider.success_response(data=loc, status=200)
    if request.method == "DELETE":
        registry.database("storagelocation", "delete", instance_id=pk, soft=False)
        return ResponseProvider.success_response(message="Deleted", status=200)
    update_data = {k: v for k, v in data.items() if k in ("parent_id", "name", "complete_name", "location_type", "barcode", "is_active", "posx", "posy", "posz")}
    if not update_data:
        return ResponseProvider.success_response(data=loc, status=200)
    try:
        updated = registry.database("storagelocation", "update", instance_id=pk, data=update_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    return ResponseProvider.success_response(data=updated, status=200)
