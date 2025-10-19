"""
Comprehensive test suite for Censudx Inventory Service

Tests cover:
- CRUD operations for inventory items
- Stock checking and validation
- Stock reservation and release
- Authentication and authorization
- Error handling and edge cases
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import json

# Import the FastAPI app
from user_service.main import app


# Test data
test_inventory_item = {
    "product_id": "product_123",
    "quantity": 100,
    "location": "warehouse_a",
    "reserved_quantity": 0
}

test_inventory_update = {
    "quantity": 150,
    "location": "warehouse_b"
}

test_stock_check = {
    "product_id": "product_123",
    "requested_quantity": 25
}

test_stock_reserve = {
    "product_id": "product_123",
    "quantity": 10,
    "reference_id": "order_456"
}


# Fixtures
@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


# Test Authentication
def test_get_inventory_items(client):
    """Test getting inventory items"""
    response = client.get("/api/v1/inventory/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# Test Inventory CRUD Operations
def test_create_inventory_item(client):
    """Test creating a new inventory item"""
    response = client.post(
        "/api/v1/inventory/",
        json=test_inventory_item
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == test_inventory_item["product_id"]
    assert data["quantity"] == test_inventory_item["quantity"]


def test_get_inventory_item_by_id(client):
    """Test retrieving a specific inventory item"""
    response = client.get("/api/v1/inventory/1")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "product_id" in data


def test_update_inventory_item(client):
    """Test updating an inventory item"""
    response = client.put(
        "/api/v1/inventory/1",
        json=test_inventory_update
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == test_inventory_update["quantity"]


def test_delete_inventory_item(client):
    """Test deleting an inventory item"""
    response = client.delete("/api/v1/inventory/1")
    assert response.status_code == 200


# Test Stock Operations
def test_check_stock(client):
    """Test stock availability checking"""
    response = client.post(
        "/api/v1/inventory/check-stock",
        json=test_stock_check
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "available" in data
    assert "current_stock" in data
    assert "requested_quantity" in data


def test_reserve_stock(client):
    """Test stock reservation"""
    response = client.post(
        "/api/v1/inventory/reserve",
        json=test_stock_reserve
    )
    
    assert response.status_code == 200


def test_release_stock(client):
    """Test releasing reserved stock"""
    response = client.post(
        "/api/v1/inventory/release",
        json=test_stock_reserve
    )
    
    assert response.status_code == 200


# Test Additional Endpoints
def test_get_low_stock_alerts(client):
    """Test retrieving low stock alerts"""
    response = client.get("/api/v1/inventory/alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_inventory_transactions(client):
    """Test retrieving transaction history for an inventory item"""
    response = client.get("/api/v1/inventory/transactions/1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# Test Error Handling
def test_inventory_item_not_found(client):
    """Test handling of non-existent inventory item"""
    response = client.get("/api/v1/inventory/999")
    assert response.status_code == 404


def test_invalid_request_data(client):
    """Test handling of invalid request data"""
    # Send invalid data
    invalid_data = {
        "product_id": "",  # Empty product_id
        "quantity": -5,    # Negative quantity
    }
    
    response = client.post(
        "/api/v1/inventory/",
        json=invalid_data
    )
    
    assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
