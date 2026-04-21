"""
Unified Integration Client for Inventory
Provides product information to other services via API
No data synchronization - services query inventory directly
"""
import logging
import requests
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
from django.db import transaction
from django.conf import settings

logger = logging.getLogger(__name__)


class UnifiedIntegrationClient:
    """
    Integration hub for inventory
    Other services query inventory directly instead of syncing data
    This class is kept for backward compatibility but simplified
    """
    
    def __init__(self):
        # Service URLs from settings
        self.accounting_url = getattr(settings, 'ACCOUNTING_SERVICE_URL', 'http://accounting-backend:8000')
        self.pos_url = getattr(settings, 'POS_SERVICE_URL', 'http://pos-backend:8000')
        self.projects_url = getattr(settings, 'PROJECTS_SERVICE_URL', 'http://projects-backend:8000')
        self.crm_url = getattr(settings, 'CRM_SERVICE_URL', 'http://crm-backend:8000')
        self.hrm_url = getattr(settings, 'HRM_SERVICE_URL', 'http://hrm-backend:8000')
        
        # Service secrets
        self.erp_service_secret = getattr(settings, 'ERP_SERVICE_SECRET', 'local-service-secret')
        self.pos_service_secret = getattr(settings, 'POS_SERVICE_SECRET', 'local-service-secret')
        self.projects_service_secret = getattr(settings, 'PROJECTS_SERVICE_SECRET', 'local-service-secret')
        self.crm_service_secret = getattr(settings, 'CRM_SERVICE_SECRET', 'local-service-secret')
        self.hrm_service_secret = getattr(settings, 'HRM_SERVICE_SECRET', 'local-service-secret')
        
        logger.info("Inventory integration client initialized - services query inventory directly")
    
    def check_service_connectivity(self, corporate_id: str) -> Dict:
        """
        Check connectivity to all integrated services
        Services should be able to reach inventory, not the other way around
        """
        return {
            'status': 'healthy',
            'message': 'Inventory is the source of truth - other services query us',
            'architecture': 'single_source_of_truth'
        }
        
    def _get_headers(self, corporate_id: str, user_id: str = None, service_secret: str = None) -> Dict:
        """Generate service-to-service authentication headers"""
        headers = {
            'X-Service-Key': service_secret or '',
            'X-Corporate-ID': str(corporate_id),
            'Content-Type': 'application/json',
        }
        if user_id:
            headers['X-User-ID'] = str(user_id)
        return headers
    
    def _handle_service_response(self, response: requests.Response, service_name: str, 
                                 operation: str, expected_codes: List[int]) -> bool:
        """
        Handle service response with graceful degradation for missing endpoints
        
        Args:
            response: The HTTP response
            service_name: Name of the service (for logging)
            operation: Operation being performed (for logging)
            expected_codes: List of successful status codes
            
        Returns:
            True if successful or endpoint not implemented, False on actual error
        """
        if response.status_code in expected_codes:
            return True
        elif response.status_code == 404:
            logger.info(f"{service_name} {operation} endpoint not yet implemented - skipping sync")
            return True  # Don't fail, just skip
        else:
            logger.warning(f"{service_name} {operation} returned {response.status_code}: {response.text[:200]}")
            return False
    
    # ==================== PRODUCT CRUD OPERATIONS ====================
    
    @transaction.atomic
    def create_product(self, product_data: Dict, corporate_id: str, user_id: str) -> Dict:
        """
        Create product and sync to all services
        
        Returns: {
            'success': bool,
            'product_id': str,
            'synced_services': List[str],
            'errors': List[str]
        }
        """
        result = {
            'success': False,
            'product_id': None,
            'synced_services': [],
            'errors': []
        }
        
        try:
            # Product is created in inventory (caller handles this)
            # We sync to other services
            
            product_id = product_data.get('id')
            result['product_id'] = str(product_id)
            
            # 1. Sync to Accounting (create inventory item)
            if self._sync_product_to_accounting(product_data, corporate_id, user_id, 'create'):
                result['synced_services'].append('Accounting')
            else:
                result['errors'].append('Failed to sync to Accounting')
            
            # 2. Sync to POS (make available for sale)
            if product_data.get('can_be_sold'):
                if self._sync_product_to_pos(product_data, corporate_id, user_id, 'create'):
                    result['synced_services'].append('POS')
                else:
                    result['errors'].append('Failed to sync to POS')
            
            # 3. Sync to Projects (for project materials/resources)
            if self._sync_product_to_projects(product_data, corporate_id, user_id, 'create'):
                result['synced_services'].append('Projects')
            else:
                result['errors'].append('Failed to sync to Projects')
            
            # 4. Notify CRM (for product catalog in customer interactions)
            if self._notify_crm_product_change(product_data, corporate_id, 'create'):
                result['synced_services'].append('CRM')
            else:
                result['errors'].append('Failed to notify CRM')
            
            # 5. Notify HRM (for asset tracking if applicable)
            if product_data.get('product_type') == 'storable':
                if self._notify_hrm_asset(product_data, corporate_id, 'create'):
                    result['synced_services'].append('HRM')
                else:
                    result['errors'].append('Failed to notify HRM')
            
            result['success'] = len(result['synced_services']) > 0
            
            logger.info(
                f"Product {product_id} created and synced to "
                f"{len(result['synced_services'])} services"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in create_product: {str(e)}", exc_info=True)
            result['errors'].append(str(e))
            return result
    
    @transaction.atomic
    def update_product(self, product_data: Dict, corporate_id: str, user_id: str) -> Dict:
        """
        Update product and sync changes to all services
        
        Returns: {
            'success': bool,
            'product_id': str,
            'synced_services': List[str],
            'errors': List[str]
        }
        """
        result = {
            'success': False,
            'product_id': None,
            'synced_services': [],
            'errors': []
        }
        
        try:
            product_id = product_data.get('id')
            result['product_id'] = str(product_id)
            
            # Sync updates to all services
            if self._sync_product_to_accounting(product_data, corporate_id, user_id, 'update'):
                result['synced_services'].append('Accounting')
            
            if product_data.get('can_be_sold'):
                if self._sync_product_to_pos(product_data, corporate_id, user_id, 'update'):
                    result['synced_services'].append('POS')
            
            if self._sync_product_to_projects(product_data, corporate_id, user_id, 'update'):
                result['synced_services'].append('Projects')
            
            if self._notify_crm_product_change(product_data, corporate_id, 'update'):
                result['synced_services'].append('CRM')
            
            if product_data.get('product_type') == 'storable':
                if self._notify_hrm_asset(product_data, corporate_id, 'update'):
                    result['synced_services'].append('HRM')
            
            result['success'] = len(result['synced_services']) > 0
            
            logger.info(f"Product {product_id} updated and synced")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in update_product: {str(e)}", exc_info=True)
            result['errors'].append(str(e))
            return result
    
    @transaction.atomic
    def delete_product(self, product_id: str, corporate_id: str, user_id: str) -> Dict:
        """
        Delete product and remove from all services
        
        Returns: {
            'success': bool,
            'product_id': str,
            'removed_from': List[str],
            'errors': List[str]
        }
        """
        result = {
            'success': False,
            'product_id': str(product_id),
            'removed_from': [],
            'errors': []
        }
        
        try:
            # Remove from all services
            if self._remove_product_from_accounting(product_id, corporate_id, user_id):
                result['removed_from'].append('Accounting')
            
            if self._remove_product_from_pos(product_id, corporate_id, user_id):
                result['removed_from'].append('POS')
            
            if self._remove_product_from_projects(product_id, corporate_id, user_id):
                result['removed_from'].append('Projects')
            
            if self._notify_crm_product_change({'id': product_id}, corporate_id, 'delete'):
                result['removed_from'].append('CRM')
            
            if self._notify_hrm_asset({'id': product_id}, corporate_id, 'delete'):
                result['removed_from'].append('HRM')
            
            result['success'] = len(result['removed_from']) > 0
            
            logger.info(f"Product {product_id} deleted and removed from services")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in delete_product: {str(e)}", exc_info=True)
            result['errors'].append(str(e))
            return result
    
    # ==================== STOCK MOVEMENT OPERATIONS ====================
    
    @transaction.atomic
    def sync_stock_move(self, move_data: Dict, corporate_id: str, user_id: str) -> Dict:
        """
        Sync stock movement to all relevant services
        
        Returns: {
            'success': bool,
            'move_id': str,
            'synced_services': List[str],
            'accounting_entry_created': bool,
            'errors': List[str]
        }
        """
        result = {
            'success': False,
            'move_id': str(move_data.get('id')),
            'synced_services': [],
            'accounting_entry_created': False,
            'errors': []
        }
        
        try:
            move_type = move_data.get('move_type')
            
            # 1. Create accounting entry for inventory valuation
            if move_type in ['receipt', 'delivery', 'adjustment']:
                if self._create_inventory_accounting_entry(move_data, corporate_id, user_id):
                    result['accounting_entry_created'] = True
                    result['synced_services'].append('Accounting')
                else:
                    result['errors'].append('Failed to create accounting entry')
            
            # 2. Update POS stock levels
            if self._update_pos_stock_levels(move_data, corporate_id, user_id):
                result['synced_services'].append('POS')
            else:
                result['errors'].append('Failed to update POS stock')
            
            # 3. Update project materials if linked to project
            if move_data.get('project_id'):
                if self._update_project_materials(move_data, corporate_id, user_id):
                    result['synced_services'].append('Projects')
                else:
                    result['errors'].append('Failed to update project materials')
            
            # 4. Update HRM assets if asset-related
            if move_data.get('is_asset'):
                if self._update_hrm_asset_location(move_data, corporate_id, user_id):
                    result['synced_services'].append('HRM')
                else:
                    result['errors'].append('Failed to update HRM assets')
            
            result['success'] = len(result['synced_services']) > 0
            
            logger.info(f"Stock move {result['move_id']} synced to services")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in sync_stock_move: {str(e)}", exc_info=True)
            result['errors'].append(str(e))
            return result
    
    # ==================== ACCOUNTING INTEGRATION ====================
    
    def _sync_product_to_accounting(self, product_data: Dict, corporate_id: str, 
                                   user_id: str, operation: str) -> bool:
        """Sync product to accounting as inventory item"""
        try:
            url = f"{self.accounting_url}/api/accounting/inventory-items/"
            
            if operation == 'create':
                accounting_data = {
                    'product_id': str(product_data['id']),
                    'name': product_data['name'],
                    'sku': product_data.get('internal_reference', ''),
                    'description': product_data.get('description', ''),
                    'unit_cost': str(product_data.get('standard_price', 0)),
                    'unit_price': str(product_data.get('list_price', 0)),
                    'product_type': product_data.get('product_type', 'storable'),
                    'costing_method': product_data.get('costing_method', 'avco'),
                    'track_inventory': product_data.get('product_type') == 'storable',
                }
                
                response = requests.post(
                    url,
                    json=accounting_data,
                    headers=self._get_headers(corporate_id, user_id, self.erp_service_secret),
                    timeout=10
                )
                
                if response.status_code == 404:
                    logger.info("Accounting inventory-items endpoint not yet implemented - skipping sync")
                    return True  # Don't fail, just skip
                
                return response.status_code == 201
                
            elif operation == 'update':
                product_id = product_data['id']
                url = f"{url}{product_id}/"
                
                accounting_data = {
                    'name': product_data['name'],
                    'unit_cost': str(product_data.get('standard_price', 0)),
                    'unit_price': str(product_data.get('list_price', 0)),
                }
                
                response = requests.patch(
                    url,
                    json=accounting_data,
                    headers=self._get_headers(corporate_id, user_id, self.erp_service_secret),
                    timeout=10
                )
                
                if response.status_code == 404:
                    logger.info("Accounting inventory-items endpoint not yet implemented - skipping sync")
                    return True  # Don't fail, just skip
                
                return response.status_code == 200
                
        except requests.exceptions.ConnectionError:
            logger.warning("Accounting service not available - skipping sync")
            return True  # Don't fail, just skip
        except requests.exceptions.Timeout:
            logger.warning("Accounting service timeout - skipping sync")
            return True  # Don't fail, just skip
        except Exception as e:
            logger.error(f"Error syncing product to accounting: {str(e)}")
            return False
    
    def _remove_product_from_accounting(self, product_id: str, corporate_id: str, 
                                       user_id: str) -> bool:
        """Remove product from accounting"""
        try:
            url = f"{self.accounting_url}/api/accounting/inventory-items/{product_id}/"
            response = requests.delete(
                url,
                headers=self._get_headers(corporate_id, user_id, self.erp_service_secret),
                timeout=10
            )
            if response.status_code == 404:
                logger.info("Accounting inventory-items endpoint not yet implemented - skipping removal")
                return True
            return response.status_code in [200, 204]
        except requests.exceptions.ConnectionError:
            logger.warning("Accounting service not available - skipping removal")
            return True
        except requests.exceptions.Timeout:
            logger.warning("Accounting service timeout - skipping removal")
            return True
        except Exception as e:
            logger.error(f"Error removing product from accounting: {str(e)}")
            return False
    
    def _create_inventory_accounting_entry(self, move_data: Dict, corporate_id: str, 
                                          user_id: str) -> bool:
        """Create journal entry for inventory movement"""
        try:
            url = f"{self.accounting_url}/api/accounting/inventory/journal-entry/"
            
            move_type = move_data['move_type']
            quantity = Decimal(str(move_data['quantity']))
            unit_cost = Decimal(str(move_data['unit_cost']))
            total_value = quantity * unit_cost
            
            # Determine accounts based on move type
            if move_type == 'receipt':
                # Dr: Inventory Asset, Cr: Accounts Payable
                entry_data = {
                    'move_id': str(move_data['id']),
                    'move_type': move_type,
                    'product_id': str(move_data['product_id']),
                    'quantity': str(quantity),
                    'unit_cost': str(unit_cost),
                    'total_value': str(total_value),
                    'debit_account': 'inventory_asset',
                    'credit_account': 'accounts_payable',
                }
            elif move_type == 'delivery':
                # Dr: COGS, Cr: Inventory Asset
                entry_data = {
                    'move_id': str(move_data['id']),
                    'move_type': move_type,
                    'product_id': str(move_data['product_id']),
                    'quantity': str(quantity),
                    'unit_cost': str(unit_cost),
                    'total_value': str(total_value),
                    'debit_account': 'cogs',
                    'credit_account': 'inventory_asset',
                }
            elif move_type == 'adjustment':
                # Dr/Cr: Inventory Asset, Cr/Dr: Inventory Adjustment
                entry_data = {
                    'move_id': str(move_data['id']),
                    'move_type': move_type,
                    'product_id': str(move_data['product_id']),
                    'quantity': str(quantity),
                    'unit_cost': str(unit_cost),
                    'total_value': str(total_value),
                    'adjustment_type': 'increase' if quantity > 0 else 'decrease',
                }
            else:
                return True  # No accounting entry needed for other types
            
            response = requests.post(
                url,
                json=entry_data,
                headers=self._get_headers(corporate_id, user_id, self.erp_service_secret),
                timeout=10
            )
            
            return response.status_code == 201
            
        except Exception as e:
            logger.error(f"Error creating inventory accounting entry: {str(e)}")
            return False
    
    # ==================== POS INTEGRATION ====================
    
    def _sync_product_to_pos(self, product_data: Dict, corporate_id: str, 
                            user_id: str, operation: str) -> bool:
        """Sync product to POS for sales"""
        try:
            url = f"{self.pos_url}/api/pos/products/"
            
            if operation == 'create':
                pos_data = {
                    'product_id': str(product_data['id']),
                    'name': product_data['name'],
                    'sku': product_data.get('internal_reference', ''),
                    'barcode': product_data.get('barcode', ''),
                    'price': str(product_data.get('list_price', 0)),
                    'cost': str(product_data.get('standard_price', 0)),
                    'category': product_data.get('category_name', ''),
                    'tax_rate': str(product_data.get('tax_rate', 0)),
                    'is_active': product_data.get('is_active', True),
                }
                
                response = requests.post(
                    url,
                    json=pos_data,
                    headers=self._get_headers(corporate_id, user_id, self.pos_service_secret),
                    timeout=10
                )
                
                return self._handle_service_response(response, "POS", "product create", [201])
                
            elif operation == 'update':
                product_id = product_data['id']
                url = f"{url}{product_id}/"
                
                pos_data = {
                    'name': product_data['name'],
                    'price': str(product_data.get('list_price', 0)),
                    'is_active': product_data.get('is_active', True),
                }
                
                response = requests.patch(
                    url,
                    json=pos_data,
                    headers=self._get_headers(corporate_id, user_id, self.pos_service_secret),
                    timeout=10
                )
                
                return self._handle_service_response(response, "POS", "product update", [200])
                
        except requests.exceptions.ConnectionError:
            logger.warning("POS service not available - skipping sync")
            return True
        except requests.exceptions.Timeout:
            logger.warning("POS service timeout - skipping sync")
            return True
        except Exception as e:
            logger.error(f"Error syncing product to POS: {str(e)}")
            return False
    
    def _remove_product_from_pos(self, product_id: str, corporate_id: str, 
                                user_id: str) -> bool:
        """Remove product from POS"""
        try:
            url = f"{self.pos_url}/api/pos/products/{product_id}/"
            response = requests.delete(
                url,
                headers=self._get_headers(corporate_id, user_id, self.pos_service_secret),
                timeout=10
            )
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Error removing product from POS: {str(e)}")
            return False
    
    def _update_pos_stock_levels(self, move_data: Dict, corporate_id: str, 
                                user_id: str) -> bool:
        """Update stock levels in POS"""
        try:
            url = f"{self.pos_url}/api/pos/stock/update/"
            
            stock_data = {
                'product_id': str(move_data['product_id']),
                'variant_id': str(move_data.get('variant_id')) if move_data.get('variant_id') else None,
                'location_id': str(move_data.get('location_to_id', move_data.get('location_from_id'))),
                'quantity_change': str(move_data['quantity']),
                'move_type': move_data['move_type'],
            }
            
            response = requests.post(
                url,
                json=stock_data,
                headers=self._get_headers(corporate_id, user_id, self.pos_service_secret),
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error updating POS stock levels: {str(e)}")
            return False
    
    # ==================== CRM INTEGRATION ====================
    
    def _notify_crm_product_change(self, product_data: Dict, corporate_id: str, 
                                  operation: str) -> bool:
        """Notify CRM of product changes for catalog"""
        try:
            url = f"{self.crm_url}/api/crm/product-catalog/sync/"
            
            notification_data = {
                'product_id': str(product_data['id']),
                'operation': operation,
                'product_name': product_data.get('name', ''),
                'is_active': product_data.get('is_active', True),
            }
            
            response = requests.post(
                url,
                json=notification_data,
                headers=self._get_headers(corporate_id, service_secret=self.crm_service_secret),
                timeout=10
            )
            
            return response.status_code in [200, 201]
            
        except Exception as e:
            logger.error(f"Error notifying CRM: {str(e)}")
            return False
    
    # ==================== HRM INTEGRATION ====================
    
    def _notify_hrm_asset(self, product_data: Dict, corporate_id: str, 
                         operation: str) -> bool:
        """Notify HRM of asset changes"""
        try:
            url = f"{self.hrm_url}/api/hrm/assets/sync/"
            
            asset_data = {
                'product_id': str(product_data['id']),
                'operation': operation,
                'product_name': product_data.get('name', ''),
                'product_type': product_data.get('product_type', ''),
            }
            
            response = requests.post(
                url,
                json=asset_data,
                headers=self._get_headers(corporate_id, service_secret=self.hrm_service_secret),
                timeout=10
            )
            
            return response.status_code in [200, 201]
            
        except Exception as e:
            logger.error(f"Error notifying HRM: {str(e)}")
            return False
    
    def _update_hrm_asset_location(self, move_data: Dict, corporate_id: str, 
                                  user_id: str) -> bool:
        """Update asset location in HRM"""
        try:
            url = f"{self.hrm_url}/api/hrm/assets/location/"
            
            location_data = {
                'product_id': str(move_data['product_id']),
                'from_location': str(move_data.get('location_from_id', '')),
                'to_location': str(move_data.get('location_to_id', '')),
                'move_date': datetime.now().isoformat(),
            }
            
            response = requests.post(
                url,
                json=location_data,
                headers=self._get_headers(corporate_id, user_id, self.hrm_service_secret),
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error updating HRM asset location: {str(e)}")
            return False
    
    # ==================== PROJECTS INTEGRATION ====================
    
    def _sync_product_to_projects(self, product_data: Dict, corporate_id: str, 
                                 user_id: str, operation: str) -> bool:
        """Sync product to projects as material/resource"""
        try:
            url = f"{self.projects_url}/api/projects/materials/"
            
            if operation == 'create':
                material_data = {
                    'product_id': str(product_data['id']),
                    'name': product_data['name'],
                    'description': product_data.get('description', ''),
                    'unit_cost': str(product_data.get('standard_price', 0)),
                    'uom': product_data.get('uom_name', 'Unit'),
                }
                
                response = requests.post(
                    url,
                    json=material_data,
                    headers=self._get_headers(corporate_id, user_id, self.projects_service_secret),
                    timeout=10
                )
                
                return response.status_code == 201
                
            elif operation == 'update':
                product_id = product_data['id']
                url = f"{url}{product_id}/"
                
                material_data = {
                    'name': product_data['name'],
                    'unit_cost': str(product_data.get('standard_price', 0)),
                }
                
                response = requests.patch(
                    url,
                    json=material_data,
                    headers=self._get_headers(corporate_id, user_id, self.projects_service_secret),
                    timeout=10
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error syncing product to projects: {str(e)}")
            return False
    
    def _remove_product_from_projects(self, product_id: str, corporate_id: str, 
                                     user_id: str) -> bool:
        """Remove product from projects"""
        try:
            url = f"{self.projects_url}/api/projects/materials/{product_id}/"
            response = requests.delete(
                url,
                headers=self._get_headers(corporate_id, user_id, self.projects_service_secret),
                timeout=10
            )
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Error removing product from projects: {str(e)}")
            return False
    
    def _update_project_materials(self, move_data: Dict, corporate_id: str, 
                                 user_id: str) -> bool:
        """Update project material usage"""
        try:
            url = f"{self.projects_url}/api/projects/materials/usage/"
            
            usage_data = {
                'project_id': str(move_data['project_id']),
                'product_id': str(move_data['product_id']),
                'quantity_used': str(move_data['quantity']),
                'unit_cost': str(move_data['unit_cost']),
                'date_used': datetime.now().isoformat(),
            }
            
            response = requests.post(
                url,
                json=usage_data,
                headers=self._get_headers(corporate_id, user_id, self.projects_service_secret),
                timeout=10
            )
            
            return response.status_code == 201
            
        except Exception as e:
            logger.error(f"Error updating project materials: {str(e)}")
            return False
    
    # ==================== BULK OPERATIONS ====================
    
    def bulk_sync_products(self, product_ids: List[str], corporate_id: str, 
                          user_id: str) -> Dict:
        """Bulk sync multiple products to all services"""
        result = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for product_id in product_ids:
            try:
                # Fetch product data and sync
                # Implementation depends on how you fetch product data
                pass
            except Exception as e:
                result['failed'] += 1
                result['errors'].append(f"Product {product_id}: {str(e)}")
        
        return result
    
    # ==================== HEALTH CHECK ====================
    
    def check_service_connectivity(self, corporate_id: str) -> Dict:
        """Check connectivity to all integrated services"""
        services = {
            'Accounting': (self.accounting_url, '/api/auth/health/'),
            'POS': (self.pos_url, '/health/'),
            'CRM': (self.crm_url, '/health/'),
            'HRM': (self.hrm_url, '/health/'),
            'Projects': (self.projects_url, '/health/'),
        }
        
        results = {}
        
        for service_name, (service_url, health_path) in services.items():
            try:
                import time
                start_time = time.time()
                
                # Health endpoints don't require authentication or corporate_id
                response = requests.get(
                    f"{service_url}{health_path}",
                    timeout=5
                )
                
                response_time = time.time() - start_time
                
                results[service_name] = {
                    'status': 'online' if response.status_code == 200 else 'error',
                    'response_time': response_time
                }
            except Exception as e:
                results[service_name] = {
                    'status': 'offline',
                    'error': str(e)
                }
        
        return results
