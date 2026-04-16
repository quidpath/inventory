"""
Client for calling the ERP backend (Accounting module) from Inventory service.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class ERPClient:
    def __init__(self):
        self.base_url = settings.ERP_BACKEND_URL
        self.service_key = getattr(settings, 'ERP_SERVICE_SECRET', '') or getattr(settings, 'INVENTORY_SERVICE_SECRET', '')

    def _headers(self):
        return {"X-Service-Key": self.service_key, "Content-Type": "application/json"}

    def create_stock_journal_entry(self, payload: dict) -> dict | None:
        """Post a journal entry to accounting for inventory valuation changes."""
        try:
            resp = requests.post(
                f"{self.base_url}/api/accounting/journal-entries/create/",
                json=payload,
                headers=self._headers(),
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("Failed to create journal entry: %s", e)
            return None
