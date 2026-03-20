from decimal import Decimal

from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from inventory_service.core.utils.request_parser import get_clean_data
from inventory_service.core.utils.response import ResponseProvider
from inventory_service.core.utils.log_base import TransactionLogBase
from inventory_service.core.services.registry import ServiceRegistry


@csrf_exempt
@require_http_methods(["GET", "POST"])
def count_list_create(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    if request.method == "GET":
        state = data.get("state") or request.GET.get("state")
        filter_data = {"corporate_id": corporate_id}
        if state:
            filter_data["state"] = state
        try:
            items = registry.database("inventorycount", "filter", data=filter_data)
        except Exception as e:
            return ResponseProvider.error_response(str(e), status=500)
        return ResponseProvider.success_response(data=items, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    if not data.get("warehouse_id") and not data.get("warehouse"):
        return ResponseProvider.error_response("Missing required field: warehouse_id", status=400)
    if not data.get("scheduled_date"):
        return ResponseProvider.error_response("Missing required field: scheduled_date", status=400)
    create_data = {
        "corporate_id": corporate_id,
        "reference": data.get("reference", ""),
        "count_type": data.get("count_type", "cycle"),
        "state": "draft",
        "warehouse_id": data.get("warehouse_id") or data.get("warehouse"),
        "scheduled_date": data.get("scheduled_date"),
        "notes": data.get("notes", ""),
        "created_by": user_id,
    }
    if data.get("location_id") is not None:
        create_data["location_id"] = data["location_id"]
    try:
        created = registry.database("inventorycount", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("inventory_count_created", user=user_id, message="Inventory count created", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
def count_detail(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        count = registry.database("inventorycount", "get", data={"id": pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found", status=404)
    if request.method == "GET":
        return ResponseProvider.success_response(data=count, status=200)
    if request.method != "PATCH":
        return ResponseProvider.method_not_allowed(["GET", "PATCH"])
    update_data = {k: v for k, v in data.items() if k in ("reference", "count_type", "state", "location_id", "scheduled_date", "notes", "done_date")}
    if not update_data:
        return ResponseProvider.success_response(data=count, status=200)
    try:
        updated = registry.database("inventorycount", "update", instance_id=pk, data=update_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    return ResponseProvider.success_response(data=updated, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def start_count(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        count = registry.database("inventorycount", "get", data={"id": pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found or not in draft state", status=404)
    if count.get("state") != "draft":
        return ResponseProvider.error_response("Count is not in draft state", status=400)
    wh = count.get("warehouse")
    warehouse_id = getattr(wh, "pk", None) if wh is not None else count.get("warehouse_id")
    loc = count.get("location")
    location_id = getattr(loc, "pk", None) if loc is not None else count.get("location_id")
    q = Q(corporate_id=corporate_id) & Q(location__warehouse_id=warehouse_id)
    if location_id:
        q = q & Q(location_id=location_id)
    try:
        levels = registry.database("stocklevel", "filter", data=q)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=500)
    existing_lines = registry.database("inventorycountline", "filter", data={"count_id": pk})
    for line in existing_lines:
        registry.database("inventorycountline", "delete", instance_id=line["id"], soft=False)
    for sl in levels:
        pid = sl.get("product_id") or (getattr(sl.get("product"), "pk", None) if sl.get("product") else None)
        vid = sl.get("variant_id") or (getattr(sl.get("variant"), "pk", None) if sl.get("variant") else None)
        lid = sl.get("location_id") or (getattr(sl.get("location"), "pk", None) if sl.get("location") else None)
        lot_id = sl.get("lot_id") or (getattr(sl.get("lot"), "pk", None) if sl.get("lot") else None)
        registry.database("inventorycountline", "create", data={
            "count_id": str(pk),
            "product_id": str(pid),
            "variant_id": str(vid) if vid else None,
            "location_id": str(lid),
            "lot_id": str(lot_id) if lot_id else None,
            "expected_qty": float(sl.get("quantity", 0)),
        })
    registry.database("inventorycount", "update", instance_id=pk, data={"state": "in_progress"})
    updated = registry.database("inventorycount", "get", data={"id": pk})
    TransactionLogBase.log("inventory_count_started", user=user_id, message="Count started", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=updated, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def submit_count_line(request, count_pk, line_pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    counted_qty = data.get("counted_qty")
    if counted_qty is None:
        return ResponseProvider.error_response("counted_qty required", status=400)
    registry = ServiceRegistry()
    try:
        count = registry.database("inventorycount", "get", data={"id": count_pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found", status=404)
    if count.get("state") != "in_progress":
        return ResponseProvider.error_response("Count not in progress", status=400)
    try:
        registry.database("inventorycountline", "update", instance_id=line_pk, data={"counted_qty": Decimal(str(counted_qty))})
    except Exception:
        return ResponseProvider.error_response("Line not found", status=404)
    line = registry.database("inventorycountline", "get", data={"id": line_pk})
    return ResponseProvider.success_response(data=line, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def validate_count(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        count = registry.database("inventorycount", "get", data={"id": pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found or not in progress", status=404)
    if count.get("state") != "in_progress":
        return ResponseProvider.error_response("Count not in progress", status=400)
    ref = count.get("reference") or str(pk)
    lines = registry.database("inventorycountline", "filter", data={"count_id": pk, "is_counted": True})
    for line in lines:
        diff = line.get("difference") or Decimal("0")
        if diff == 0:
            continue
        try:
            product = registry.database("product", "get", data={"id": line["product_id"]})
        except Exception:
            continue
        uom_id = product.get("uom_id") or (getattr(product.get("uom"), "pk", None) if product.get("uom") else None)
        move_data = {
            "corporate_id": corporate_id,
            "reference": f"INV/{ref}",
            "move_type": "adjustment",
            "product_id": str(line["product_id"]),
            "variant_id": str(line["variant_id"]) if line.get("variant_id") else None,
            "lot_id": str(line["lot_id"]) if line.get("lot_id") else None,
            "uom_id": str(uom_id),
            "quantity": float(abs(diff)),
            "state": "done",
            "done_date": timezone.now().isoformat(),
        }
        if diff > 0:
            move_data["location_to_id"] = str(line["location_id"])
        else:
            move_data["location_from_id"] = str(line["location_id"])
        try:
            registry.database("stockmove", "create", data=move_data)
        except Exception:
            pass
        flt = {"corporate_id": corporate_id, "product_id": line["product_id"], "location_id": line["location_id"]}
        if line.get("variant_id"):
            flt["variant_id"] = line["variant_id"]
        if line.get("lot_id"):
            flt["lot_id"] = line["lot_id"]
        levels = registry.database("stocklevel", "filter", data=flt)
        qty = float(line.get("counted_qty", 0))
        if levels:
            registry.database("stocklevel", "update", instance_id=levels[0]["id"], data={"quantity": qty})
        else:
            registry.database("stocklevel", "create", data={
                "corporate_id": corporate_id,
                "product_id": str(line["product_id"]),
                "variant_id": str(line.get("variant_id")) if line.get("variant_id") else None,
                "location_id": str(line["location_id"]),
                "lot_id": str(line.get("lot_id")) if line.get("lot_id") else None,
                "quantity": qty,
                "reserved_quantity": 0,
            })
    registry.database("inventorycount", "update", instance_id=pk, data={"state": "done", "done_date": timezone.now().date().isoformat()})
    updated = registry.database("inventorycount", "get", data={"id": pk})
    TransactionLogBase.log("inventory_count_validated", user=user_id, message="Count validated", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=updated, status=200)
