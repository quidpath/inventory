from django.urls import path

from .views import current_valuation, generate_valuation_report, valuation_layers, valuation_report_list

urlpatterns = [
    path("layers/", valuation_layers),
    path("current/", current_valuation),
    path("reports/", valuation_report_list),
    path("reports/generate/", generate_valuation_report),
]
