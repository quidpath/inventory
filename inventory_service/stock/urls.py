from django.urls import path

from .views.lots_serials import lot_detail, lot_list_create, serial_detail, serial_list_create
from .views.stock_moves import (
    cancel_move,
    reorder_rule_detail,
    reorder_rule_list_create,
    stock_level_list,
    stock_move_detail,
    stock_move_list_create,
    stock_summary,
    validate_move,
)

urlpatterns = [
    path("moves/", stock_move_list_create),
    path("moves/<uuid:pk>/", stock_move_detail),
    path("moves/<uuid:pk>/validate/", validate_move),
    path("moves/<uuid:pk>/cancel/", cancel_move),
    path("levels/", stock_level_list),
    path("summary/<uuid:product_pk>/", stock_summary),
    path("reorder-rules/", reorder_rule_list_create),
    path("reorder-rules/<uuid:pk>/", reorder_rule_detail),
    path("lots/", lot_list_create),
    path("lots/<uuid:pk>/", lot_detail),
    path("serials/", serial_list_create),
    path("serials/<uuid:pk>/", serial_detail),
]
