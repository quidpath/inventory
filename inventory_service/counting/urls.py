from django.urls import path

from .views import count_detail, count_list_create, start_count, submit_count_line, validate_count

urlpatterns = [
    path("", count_list_create),
    path("<uuid:pk>/", count_detail),
    path("<uuid:pk>/start/", start_count),
    path("<uuid:pk>/validate/", validate_count),
    path("<uuid:count_pk>/lines/<uuid:line_pk>/submit/", submit_count_line),
]
