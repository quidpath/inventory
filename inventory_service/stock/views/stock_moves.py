import logging
from decimal import Decimal

from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from inventory_service.core.utils.request_parser import get_clean_data
from inventory_service.core.utils.response import ResponseProvider
from inventory_service.core.utils.log_base import TransactionLogBase
from inventory_service.core.services.registry import ServiceRegistry

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def stock_move_list_create(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    if request.method == "GET":
        q = Q(corporate_id=corporate_id)
        if data.get("type") or request.GET.get("type"):
            q &= Q(move_type=data.get("type") or request.GET.get("type"))
        if data.get("state") or request.GET.get("state"):
            q &= Q(state=data.get("state") or request.GET.get("state"))
        if data.get("product") or request.GET.get("product"):
            q &= Q(product_id=data.get("product") or request.GET.get("product"))
        if data.get("reference") or request.GET.get("reference"):
            q &= Q(reference__icontains=data.get("reference") or request.GET.get("reference"))
        items = registry.database("stockmove", "filter", data=q)
        items = items[:200] if isinstance(items, list) else items
        return ResponseProvider.success_response(data=items, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    create_data = {k: v for k, v in data.items() if k in (
        "reference", "move_type", "product_id", "variant_id", "lot_id", "serial_id",
        "location_from_id", "location_to_id", "quantity", "uom_id", "unit_cost",
        "scheduled_date", "notes"
    )}
    create_data["corporate_id"] = corporate_id
    create_data["created_by"] = user_id
    create_data.setdefault("state", "draft")
    try:
        created = registry.database("stockmove", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("stock_move_created", user=user_id, message="Stock move created", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
def stock_move_detail(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        move = registry.database("stockmove", "get", data={"id": pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found", status=404)
    if request.method == "GET":
        return ResponseProvider.success_response(data=move, status=200)
    update_data = {k: v for k, v in data.items() if k in (
        "reference", "move_type", "product_id", "variant_id", "lot_id", "serial_id",
        "location_from_id", "location_to_id", "quantity", "uom_id", "unit_cost",
        "scheduled_date", "notes"
    )}
    if not update_data:
        return ResponseProvider.success_response(data=move, status=200)
    try:
        updated = registry.database("stockmove", "update", instance_id=pk, data=update_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    return ResponseProvider.success_response(data=updated, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def validate_move(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    from inventory_service.stock.models import StockMove
    try:
        move = StockMove.objects.get(pk=pk, corporate_id=corporate_id)
    except StockMove.DoesNotExist:
        return ResponseProvider.error_response("Not found", status=404)
    try:
        if move.state == "draft":
            move.confirm()
        move.validate()
    except ValueError as e:
        return ResponseProvider.error_response(str(e), status=400)
    registry = ServiceRegistry()
    updated = registry.database("stockmove", "get", data={"id": pk})
    TransactionLogBase.log("stock_move_validated", user=user_id, message="Stock move validated", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=updated, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def cancel_move(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        move = registry.database("stockmove", "get", data={"id": pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found", status=404)
    if move.get("state") == "done":
        return ResponseProvider.error_response("Cannot cancel a done move", status=400)
    registry.database("stockmove", "update", instance_id=pk, data={"state": "cancelled"})
    updated = registry.database("stockmove", "get", data={"id": pk})
    return ResponseProvider.success_response(data=updated, status=200)


@csrf_exempt
@require_http_methods(["GET"])
def stock_level_list(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    q = Q(corporate_id=corporate_id)
    if data.get("product") or request.GET.get("product"):
        q &= Q(product_id=data.get("product") or request.GET.get("product"))
    if data.get("location") or request.GET.get("location"):
        q &= Q(location_id=data.get("location") or request.GET.get("location"))
    if data.get("warehouse") or request.GET.get("warehouse"):
        q &= Q(location__warehouse_id=data.get("warehouse") or request.GET.get("warehouse"))
    if (data.get("zero_only") or request.GET.get("zero_only", "false")).lower() != "true":
        q &= Q(quantity__gt=0)
    items = registry.database("stocklevel", "filter", data=q)
    return ResponseProvider.success_response(data=items, status=200)


@csrf_exempt
@require_http_methods(["GET"])
def stock_summary(request, product_pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    levels = registry.database("stocklevel", "filter", data={"corporate_id": corporate_id, "product_id": product_pk})
    total_qty = sum(Decimal(str(l.get("quantity", 0))) for l in levels)
    total_reserved = sum(Decimal(str(l.get("reserved_quantity", 0))) for l in levels)
    by_location = [l for l in levels if Decimal(str(l.get("quantity", 0))) > 0]
    return ResponseProvider.success_response(data={
        "product_id": str(product_pk),
        "total_quantity": float(total_qty),
        "total_reserved": float(total_reserved),
        "available": float(total_qty - total_reserved),
        "by_location": by_location,
    }, status=200)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def reorder_rule_list_create(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    if request.method == "GET":
        items = registry.database("reorderrule", "filter", data={"corporate_id": corporate_id})
        return ResponseProvider.success_response(data=items, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    create_data = {k: v for k, v in data.items() if k in ("product_id", "variant_id", "location_id", "min_qty", "max_qty", "reorder_qty", "is_active")}
    create_data["corporate_id"] = corporate_id
    try:
        created = registry.database("reorderrule", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("reorder_rule_created", user=user_id, message="Reorder rule created", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def reorder_rule_detail(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        rule = registry.database("reorderrule", "get", data={"id": pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found", status=404)
    if request.method == "GET":
        return ResponseProvider.success_response(data=rule, status=200)
    if request.method == "DELETE":
        registry.database("reorderrule", "delete", instance_id=pk, soft=False)
        return ResponseProvider.success_response(message="Deleted", status=200)
    update_data = {k: v for k, v in data.items() if k in ("product_id", "variant_id", "location_id", "min_qty", "max_qty", "reorder_qty", "is_active")}
    if not update_data:
        return ResponseProvider.success_response(data=rule, status=200)
    try:
        updated = registry.database("reorderrule", "update", instance_id=pk, data=update_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    return ResponseProvider.success_response(data=updated, status=200)
