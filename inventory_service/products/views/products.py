import logging

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
def product_list_create(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    if request.method == "GET":
        q = Q(corporate_id=corporate_id)
        search = data.get("search") or request.GET.get("search")
        if search:
            q &= Q(name__icontains=search) | Q(barcode__icontains=search) | Q(internal_reference__icontains=search)
        if data.get("type") or request.GET.get("type"):
            q &= Q(product_type=data.get("type") or request.GET.get("type"))
        if data.get("category") or request.GET.get("category"):
            q &= Q(category_id=data.get("category") or request.GET.get("category"))
        is_active = data.get("is_active") if "is_active" in data else request.GET.get("is_active")
        if is_active is not None:
            q &= Q(is_active=is_active.lower() == "true")
        items = registry.database("product", "filter", data=q)
        count = len(items) if isinstance(items, list) else 0
        return ResponseProvider.success_response(data={"count": count, "results": items}, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    create_data = {k: v for k, v in data.items() if k in (
        "internal_reference", "name", "description", "description_purchase", "description_sale",
        "product_type", "category_id", "uom_id", "uom_purchase_id", "costing_method",
        "standard_price", "list_price", "taxes_included", "tax_rate", "weight", "volume",
        "barcode", "hs_code", "is_active", "can_be_sold", "can_be_purchased",
        "track_lots", "track_serials", "expiry_tracking", "shelf_life_days", "min_qty", "reorder_qty"
    )}
    create_data["corporate_id"] = corporate_id
    create_data["created_by"] = user_id
    try:
        created = registry.database("product", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("product_created", user=user_id, message="Product created", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def product_detail(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        product = registry.database("product", "get", data={"id": pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Product not found", status=404)
    if request.method == "GET":
        return ResponseProvider.success_response(data=product, status=200)
    if request.method == "DELETE":
        registry.database("product", "delete", instance_id=pk, soft=False)
        return ResponseProvider.success_response(message="Deleted", status=200)
    update_data = {k: v for k, v in data.items() if k in (
        "internal_reference", "name", "description", "description_purchase", "description_sale",
        "product_type", "category_id", "uom_id", "uom_purchase_id", "costing_method",
        "standard_price", "list_price", "taxes_included", "tax_rate", "weight", "volume",
        "barcode", "hs_code", "is_active", "can_be_sold", "can_be_purchased",
        "track_lots", "track_serials", "expiry_tracking", "shelf_life_days", "min_qty", "reorder_qty"
    )}
    if not update_data:
        return ResponseProvider.success_response(data=product, status=200)
    try:
        updated = registry.database("product", "update", instance_id=pk, data=update_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    return ResponseProvider.success_response(data=updated, status=200)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def variant_list_create(request, product_pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        product = registry.database("product", "get", data={"id": product_pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Product not found", status=404)
    if request.method == "GET":
        items = registry.database("productvariant", "filter", data={"product_id": product_pk, "is_active": True})
        return ResponseProvider.success_response(data=items, status=200)
    if request.method != "POST":
        return ResponseProvider.method_not_allowed(["GET", "POST"])
    create_data = {k: v for k, v in data.items() if k in (
        "combination", "sku", "barcode", "internal_reference", "standard_price", "list_price",
        "weight", "volume", "image", "is_active"
    )}
    create_data["product_id"] = product_pk
    try:
        created = registry.database("productvariant", "create", data=create_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    TransactionLogBase.log("product_variant_created", user=user_id, message="Product variant created", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def variant_detail(request, pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    items = registry.database("productvariant", "filter", data=Q(pk=pk) & Q(product__corporate_id=corporate_id))
    variant = items[0] if isinstance(items, list) and items else None
    if not variant:
        return ResponseProvider.error_response("Variant not found", status=404)
    if request.method == "GET":
        return ResponseProvider.success_response(data=variant, status=200)
    if request.method == "DELETE":
        registry.database("productvariant", "update", instance_id=pk, data={"is_active": False})
        return ResponseProvider.success_response(message="Deactivated", status=200)
    update_data = {k: v for k, v in data.items() if k in (
        "combination", "sku", "barcode", "internal_reference", "standard_price", "list_price",
        "weight", "volume", "image", "is_active"
    )}
    if not update_data:
        return ResponseProvider.success_response(data=variant, status=200)
    try:
        updated = registry.database("productvariant", "update", instance_id=pk, data=update_data)
    except Exception as e:
        return ResponseProvider.error_response(str(e), status=400)
    return ResponseProvider.success_response(data=updated, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def upload_product_image(request, product_pk):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    user_id = metadata.get("user_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    registry = ServiceRegistry()
    try:
        product = registry.database("product", "get", data={"id": product_pk, "corporate_id": corporate_id})
    except Exception:
        return ResponseProvider.error_response("Product not found", status=404)
    image_file = request.FILES.get("image")
    if not image_file:
        return ResponseProvider.error_response("No image provided", status=400)
    from inventory_service.products.models import Product, ProductImage
    product_obj = Product.objects.get(pk=product_pk)
    is_primary = not product_obj.images.filter(is_primary=True).exists()
    img = ProductImage.objects.create(
        product=product_obj,
        image=image_file,
        alt_text=data.get("alt_text", ""),
        is_primary=is_primary,
    )
    created = registry.serialize_instance(img)
    TransactionLogBase.log("product_image_uploaded", user=user_id, message="Product image uploaded", state_name="Completed", request=request)
    return ResponseProvider.success_response(data=created, message="Created", status=201)


@csrf_exempt
@require_http_methods(["GET"])
def product_by_barcode(request):
    data, metadata = get_clean_data(request)
    corporate_id = metadata.get("corporate_id")
    if not corporate_id:
        return ResponseProvider.error_response("Unauthorized", status=401)
    barcode = (data.get("barcode") or request.GET.get("barcode") or "").strip()
    if not barcode:
        return ResponseProvider.error_response("barcode required", status=400)
    registry = ServiceRegistry()
    from django.db.models import Q
    variants = registry.database("productvariant", "filter", data=Q(barcode=barcode) & Q(product__corporate_id=corporate_id) & Q(is_active=True))
    if variants and isinstance(variants, list):
        return ResponseProvider.success_response(data={"type": "variant", "data": variants[0]}, status=200)
    products = registry.database("product", "filter", data={"barcode": barcode, "corporate_id": corporate_id, "is_active": True})
    if products and isinstance(products, list):
        return ResponseProvider.success_response(data={"type": "product", "data": products[0]}, status=200)
    return ResponseProvider.error_response("Not found", status=404)
