from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from inventory_service.core.utils.request_parser import get_clean_data
from inventory_service.core.utils.response import ResponseProvider
from inventory_service.core.utils.log_base import TransactionLogBase
from inventory_service.core.services.registry import ServiceRegistry


@csrf_exempt
@require_http_methods(["GET", "POST"])
def lot_list_create(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    if request.method == "GET":
        filter_data = {"corporate_id": corporate_id}
        if data.get("product_id") or request.GET.get("product_id"):
            filter_data["product_id"] = data.get("product_id") or request.GET.get("product_id")
        if request.GET.get("expired") == "true":
            from django.db.models import Q
            items = registry.database("stocklot", "filter", data=Q(corporate_id=corporate_id) & Q(expiry_date__lt=timezone.now().date()))
        else:
            items = registry.database("stocklot", "filter", data=filter_data)
        return ResponseProvider.success_response(data=items, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    create_data = {k: v for k, v in data.items() if k in ("product_id", "lot_number", "expiry_date", "manufacture_date", "supplier_lot", "notes", "is_active")}
    create_data["corporate_id"] = corporate_id
    try:
        created = registry.database("stocklot", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("stock_lot_created", user=user_id, message="Stock lot created", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH"])
def lot_detail(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        lot = registry.database("stocklot", "get", data={"id": pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found", status=404)
    if request.method == "GET":
        return ResponseProvider.success_response(data=lot, status=200)
    update_data = {k: v for k, v in data.items() if k in ("lot_number", "expiry_date", "manufacture_date", "supplier_lot", "notes", "is_active")}
    if not update_data:
        return ResponseProvider.success_response(data=lot, status=200)
    try:
        updated = registry.database("stocklot", "update", instance_id=pk, data=update_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    return ResponseProvider.success_response(data=updated, status=200)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def serial_list_create(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    if request.method == "GET":
        filter_data = {"corporate_id": corporate_id}
        if data.get("product_id") or request.GET.get("product_id"):
            filter_data["product_id"] = data.get("product_id") or request.GET.get("product_id")
        if data.get("state") or request.GET.get("state"):
            filter_data["state"] = data.get("state") or request.GET.get("state")
        items = registry.database("serialnumber", "filter", data=filter_data)
        return ResponseProvider.success_response(data=items, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    create_data = {k: v for k, v in data.items() if k in ("product_id", "variant_id", "serial_number", "state", "location_id", "lot_id", "notes")}
    create_data["corporate_id"] = corporate_id
    try:
        created = registry.database("serialnumber", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("serial_number_created", user=user_id, message="Serial number created", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH"])
def serial_detail(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        sn = registry.database("serialnumber", "get", data={"id": pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found", status=404)
    if request.method == "GET":
        return ResponseProvider.success_response(data=sn, status=200)
    update_data = {k: v for k, v in data.items() if k in ("serial_number", "state", "location_id", "lot_id", "notes")}
    if not update_data:
        return ResponseProvider.success_response(data=sn, status=200)
    try:
        updated = registry.database("serialnumber", "update", instance_id=pk, data=update_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    return ResponseProvider.success_response(data=updated, status=200)
