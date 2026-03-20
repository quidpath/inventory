from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from inventory_service.core.utils.request_parser import get_clean_data
from inventory_service.core.utils.response import ResponseProvider
from inventory_service.core.utils.log_base import TransactionLogBase
from inventory_service.core.services.registry import ServiceRegistry


@csrf_exempt
@require_http_methods(["GET", "POST"])
def category_list_create(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    if request.method == "GET":
        items = registry.database("category", "filter", data={"corporate_id": corporate_id, "parent": None})
        return ResponseProvider.success_response(data=items, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    create_data = {k: v for k, v in data.items() if k in ("name", "slug", "parent_id", "description", "image", "is_active")}
    create_data["corporate_id"] = corporate_id
    try:
        created = registry.database("category", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("category_created", user=user_id, message="Category created", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def category_detail(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        cat = registry.database("category", "get", data={"id": pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found", status=404)
    if request.method == "GET":
        return ResponseProvider.success_response(data=cat, status=200)
    if request.method == "DELETE":
        registry.database("category", "delete", instance_id=pk, soft=False)
        return ResponseProvider.success_response(message="Deleted", status=200)
    update_data = {k: v for k, v in data.items() if k in ("name", "slug", "parent_id", "description", "image", "is_active")}
    if not update_data:
        return ResponseProvider.success_response(data=cat, status=200)
    try:
        updated = registry.database("category", "update", instance_id=pk, data=update_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    return ResponseProvider.success_response(data=updated, status=200)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def uom_list_create(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    if request.method == "GET":
        items = registry.database("unitofmeasure", "filter", data={"corporate_id": corporate_id})
        return ResponseProvider.success_response(data=items, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    create_data = {k: v for k, v in data.items() if k in ("category_id", "name", "symbol", "factor", "rounding", "is_base", "is_active")}
    create_data["corporate_id"] = corporate_id
    try:
        created = registry.database("unitofmeasure", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("uom_created", user=user_id, message="UoM created", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def uom_detail(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        uom = registry.database("unitofmeasure", "get", data={"id": pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found", status=404)
    if request.method == "GET":
        return ResponseProvider.success_response(data=uom, status=200)
    if request.method == "DELETE":
        registry.database("unitofmeasure", "delete", instance_id=pk, soft=False)
        return ResponseProvider.success_response(message="Deleted", status=200)
    update_data = {k: v for k, v in data.items() if k in ("category_id", "name", "symbol", "factor", "rounding", "is_base", "is_active")}
    if not update_data:
        return ResponseProvider.success_response(data=uom, status=200)
    try:
        updated = registry.database("unitofmeasure", "update", instance_id=pk, data=update_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    return ResponseProvider.success_response(data=updated, status=200)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def attribute_list_create(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    if request.method == "GET":
        items = registry.database("productattribute", "filter", data={"corporate_id": corporate_id})
        return ResponseProvider.success_response(data=items, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    create_data = {k: v for k, v in data.items() if k in ("name", "display_type", "sequence")}
    create_data["corporate_id"] = corporate_id
    try:
        created = registry.database("productattribute", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("product_attribute_created", user=user_id, message="Product attribute created", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def attribute_value_list(request, attribute_pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        attr = registry.database("productattribute", "get", data={"id": attribute_pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found", status=404)
    if request.method == "GET":
        items = registry.database("attributevalue", "filter", data={"attribute_id": attribute_pk})
        return ResponseProvider.success_response(data=items, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    create_data = {k: v for k, v in data.items() if k in ("name", "color_code", "sequence")}
    create_data["attribute_id"] = attribute_pk
    try:
        created = registry.database("attributevalue", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("attribute_value_created", user=user_id, message="Attribute value created", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def pricelist_list_create(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    if request.method == "GET":
        items = registry.database("pricelist", "filter", data={"corporate_id": corporate_id})
        return ResponseProvider.success_response(data=items, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    create_data = {k: v for k, v in data.items() if k in ("name", "currency", "is_default", "date_start", "date_end", "is_active")}
    create_data["corporate_id"] = corporate_id
    try:
        created = registry.database("pricelist", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("pricelist_created", user=user_id, message="Price list created", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def pricelist_detail(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        pl = registry.database("pricelist", "get", data={"id": pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found", status=404)
    if request.method == "GET":
        items = registry.database("pricelistitem", "filter", data={"pricelist_id": pk})
        pl["items"] = items
        return ResponseProvider.success_response(data=pl, status=200)
    if request.method == "DELETE":
        registry.database("pricelist", "delete", instance_id=pk, soft=False)
        return ResponseProvider.success_response(message="Deleted", status=200)
    update_data = {k: v for k, v in data.items() if k in ("name", "currency", "is_default", "date_start", "date_end", "is_active")}
    if not update_data:
        return ResponseProvider.success_response(data=pl, status=200)
    try:
        updated = registry.database("pricelist", "update", instance_id=pk, data=update_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    return ResponseProvider.success_response(data=updated, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def pricelist_add_item(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        pl = registry.database("pricelist", "get", data={"id": pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Not found", status=404)
    create_data = {k: v for k, v in data.items() if k in ("product_id", "variant_id", "category_id", "compute_method", "fixed_price", "discount_percent", "min_qty", "date_start", "date_end")}
    create_data["pricelist_id"] = pk
    try:
        created = registry.database("pricelistitem", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("pricelist_item_added", user=user_id, message="Price list item added", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)
