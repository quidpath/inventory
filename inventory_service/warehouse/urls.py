from django.urls import path

from .views.warehouse import location_detail, location_list_create, warehouse_detail, warehouse_list_create

urlpatterns = [
    path("", warehouse_list_create),
    path("<uuid:pk>/", warehouse_detail),
    path("<uuid:warehouse_pk>/locations/", location_list_create),
    path("locations/<uuid:pk>/", location_detail),
]
