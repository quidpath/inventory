"""
Integration tests for Inventory Service
Tests Products, Stock, Warehouses, Pricelists, Categories, UOM
"""
import requests
import pytest
import uuid


BASE_URL = "http://localhost:8004"


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/health/")
        assert response.status_code == 200


class TestProductEndpoints:
    """Test Product CRUD endpoints"""

    def test_list_products_requires_auth(self):
        """Test listing products requires authentication"""
        response = requests.get(f"{BASE_URL}/api/inventory/products/")
        assert response.status_code in [401, 403]

    def test_create_product_requires_auth(self):
        """Test creating product requires authentication"""
        data = {
            "name": "Test Product",
            "sku": "TEST-001",
            "price": "100.00",
        }
        response = requests.post(f"{BASE_URL}/api/inventory/products/", json=data)
        assert response.status_code in [400, 401, 403]

    def test_get_product_detail_requires_auth(self):
        """Test retrieving product detail requires authentication"""
        product_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/inventory/products/{product_id}/"
        )
        assert response.status_code in [401, 403, 404]

    def test_update_product_requires_auth(self):
        """Test updating product requires authentication"""
        product_id = str(uuid.uuid4())
        data = {"name": "Updated Product"}
        response = requests.patch(
            f"{BASE_URL}/api/inventory/products/{product_id}/", json=data
        )
        assert response.status_code in [401, 403, 404]

    def test_delete_product_requires_auth(self):
        """Test deleting product requires authentication"""
        product_id = str(uuid.uuid4())
        response = requests.delete(
            f"{BASE_URL}/api/inventory/products/{product_id}/"
        )
        assert response.status_code in [401, 403, 404]


class TestCategoryEndpoints:
    """Test Category endpoints"""

    def test_list_categories_requires_auth(self):
        """Test listing categories requires authentication"""
        response = requests.get(f"{BASE_URL}/api/inventory/products/categories/")
        assert response.status_code in [401, 403, 404]

    def test_create_category_requires_auth(self):
        """Test creating category requires authentication"""
        data = {"name": "Test Category"}
        response = requests.post(
            f"{BASE_URL}/api/inventory/products/categories/", json=data
        )
        assert response.status_code in [400, 401, 403, 404]


class TestWarehouseEndpoints:
    """Test Warehouse CRUD endpoints"""

    def test_list_warehouses_requires_auth(self):
        """Test listing warehouses requires authentication"""
        response = requests.get(f"{BASE_URL}/api/inventory/warehouse/")
        assert response.status_code in [401, 403]

    def test_create_warehouse_requires_auth(self):
        """Test creating warehouse requires authentication"""
        data = {
            "name": "Test Warehouse",
            "location": "Test Location",
        }
        response = requests.post(
            f"{BASE_URL}/api/inventory/warehouse/", json=data
        )
        assert response.status_code in [400, 401, 403]


class TestStockEndpoints:
    """Test Stock management endpoints"""

    def test_list_stock_requires_auth(self):
        """Test listing stock requires authentication"""
        response = requests.get(f"{BASE_URL}/api/inventory/stock/")
        assert response.status_code in [401, 403]

    def test_create_stock_adjustment_requires_auth(self):
        """Test creating stock adjustment requires authentication"""
        data = {
            "product_id": str(uuid.uuid4()),
            "warehouse_id": str(uuid.uuid4()),
            "quantity": 10,
            "type": "adjustment",
        }
        response = requests.post(f"{BASE_URL}/api/inventory/stock/", json=data)
        assert response.status_code in [400, 401, 403]


class TestValuationEndpoints:
    """Test Inventory Valuation endpoints"""

    def test_get_valuation_requires_auth(self):
        """Test getting inventory valuation requires authentication"""
        response = requests.get(f"{BASE_URL}/api/inventory/valuation/")
        assert response.status_code in [401, 403, 404]
