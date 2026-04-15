from django.urls import path

from .views.categories import (
    attribute_list_create,
    attribute_value_list,
    category_detail,
    category_list_create,
    pricelist_add_item,
    pricelist_detail,
    pricelist_list_create,
    uom_detail,
    uom_list_create,
)
from .views.products import (
    product_by_barcode,
    product_detail,
    product_list_create,
    upload_product_image,
    variant_detail,
    variant_list_create,
)
from .views.summary import inventory_summary

urlpatterns = [
    path("summary/", inventory_summary, name="inventory_summary"),
    path("", product_list_create),
    path("<uuid:pk>/", product_detail),
    path("<uuid:product_pk>/variants/", variant_list_create),
    path("variants/<uuid:pk>/", variant_detail),
    path("<uuid:product_pk>/images/", upload_product_image),
    path("barcode/", product_by_barcode),
    path("categories/", category_list_create),
    path("categories/<uuid:pk>/", category_detail),
    path("uom/", uom_list_create),
    path("uom/<uuid:pk>/", uom_detail),
    path("attributes/", attribute_list_create),
    path("attributes/<uuid:attribute_pk>/values/", attribute_value_list),
    path("pricelists/", pricelist_list_create),
    path("pricelists/<uuid:pk>/", pricelist_detail),
    path("pricelists/<uuid:pk>/items/", pricelist_add_item),
]
