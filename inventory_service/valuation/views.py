from decimal import Decimal

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from inventory_service.core.utils.request_parser import get_clean_data
from inventory_service.core.utils.response import ResponseProvider
from inventory_service.core.utils.log_base import TransactionLogBase
from inventory_service.core.services.registry import ServiceRegistry


@csrf_exempt
@require_http_methods(["GET"])
def valuation_layers(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    filter_data = {"corporate_id": corporate_id}
    if data.get("product_id") or request.GET.get("product_id"):
        filter_data["product_id"] = data.get("product_id") or request.GET.get("product_id")
    try:
        items = registry.database("stockvaluationlayer", "filter", data=filter_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=500)
    return ResponseProvider.success_response(data=items[:200] if isinstance(items, list) else items, status=200)


@csrf_exempt
@require_http_methods(["GET"])
def current_valuation(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        products = registry.database("product", "filter", data={"corporate_id": corporate_id, "product_type": "storable", "is_active": True})
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=500)
    levels = registry.database("stocklevel", "filter", data={"corporate_id": corporate_id})
    by_product = {}
    for sl in levels:
        pid = str(sl.get("product_id") or sl.get("product"))
        by_product[pid] = by_product.get(pid, Decimal("0")) + Decimal(str(sl.get("quantity", 0)))
    lines = []
    total = Decimal("0")
    for p in products:
        pid = str(p.get("id"))
        qty = by_product.get(pid, Decimal("0"))
        standard_price = Decimal(str(p.get("standard_price", 0)))
        value = qty * standard_price
        total += value
        lines.append({
            "product_id": pid,
            "product_name": p.get("name", ""),
            "quantity": str(qty),
            "unit_cost": str(standard_price),
            "total_value": str(value),
            "costing_method": p.get("costing_method", ""),
        })
    return ResponseProvider.success_response(data={"total_value": str(total), "currency": "KES", "lines": lines}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def generate_valuation_report(request):
    import datetime
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    report_date = data.get("report_date", datetime.date.today().isoformat())
    registry = ServiceRegistry()
    try:
        products = registry.database("product", "filter", data={"corporate_id": corporate_id, "product_type": "storable", "is_active": True})
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=500)
    levels = registry.database("stocklevel", "filter", data={"corporate_id": corporate_id})
    by_product = {}
    for sl in levels:
        pid = str(sl.get("product_id") or sl.get("product"))
        by_product[pid] = by_product.get(pid, Decimal("0")) + Decimal(str(sl.get("quantity", 0)))
    lines = []
    total = Decimal("0")
    for p in products:
        pid = str(p.get("id"))
        qty = by_product.get(pid, Decimal("0"))
        standard_price = Decimal(str(p.get("standard_price", 0)))
        value = qty * standard_price
        total += value
        lines.append({
            "product_id": pid,
            "product_name": p.get("name", ""),
            "quantity": str(qty),
            "unit_cost": str(standard_price),
            "total_value": str(value),
        })
    try:
        created = registry.database("inventoryvaluationreport", "create", data={
            "corporate_id": corporate_id,
            "report_date": report_date,
            "total_value": float(total),
            "lines": lines,
        })
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("valuation_report_generated", user=user_id, message="Valuation report generated", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET"])
def valuation_report_list(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        items = registry.database("inventoryvaluationreport", "filter", data={"corporate_id": corporate_id})
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=500)
    return ResponseProvider.success_response(data=items, status=200)
