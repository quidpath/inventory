"""
Conftest for inventory integration tests
"""
import pytest


@pytest.fixture
def inventory_url():
    return "http://localhost:8004"
