"""
User cache service — fetches and caches user/corporate data from ERP backend.
Mirrors the same pattern used in the billing service.
"""
import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class UserCacheService:
    def get_user_data(self, user_id):
        cache_key = f"user_{user_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        try:
            url = f"{settings.ERP_BACKEND_URL}/api/auth/users/{user_id}/"
            # Use ERP_SERVICE_SECRET for authentication with accounting service
            service_key = getattr(settings, 'ERP_SERVICE_SECRET', '') or getattr(settings, 'INVENTORY_SERVICE_SECRET', '')
            if not service_key:
                logger.error("ERP_SERVICE_SECRET not configured")
                return None
                
            resp = requests.get(
                url,
                headers={"X-Service-Key": service_key},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                cache.set(cache_key, data, settings.USER_CACHE_TTL)
                return data
            else:
                logger.warning("Failed to fetch user %s: HTTP %s - %s", user_id, resp.status_code, resp.text)
        except Exception as e:
            logger.warning("Could not fetch user %s: %s", user_id, e)
        return None

    def get_corporate_data(self, corporate_id):
        cache_key = f"corporate_{corporate_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        try:
            url = f"{settings.ERP_BACKEND_URL}/api/auth/corporates/{corporate_id}/"
            # Use ERP_SERVICE_SECRET for authentication with accounting service
            service_key = getattr(settings, 'ERP_SERVICE_SECRET', '') or getattr(settings, 'INVENTORY_SERVICE_SECRET', '')
            if not service_key:
                logger.error("ERP_SERVICE_SECRET not configured")
                return None
                
            resp = requests.get(
                url,
                headers={"X-Service-Key": service_key},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                cache.set(cache_key, data, settings.CORPORATE_CACHE_TTL)
                return data
            else:
                logger.warning("Failed to fetch corporate %s: HTTP %s - %s", corporate_id, resp.status_code, resp.text)
        except Exception as e:
            logger.warning("Could not fetch corporate %s: %s", corporate_id, e)
        return None
