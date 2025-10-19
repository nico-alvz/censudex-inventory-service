"""
RabbitMQ Integration Tests for Censudx Inventory Service
"""

import pytest
import asyncio
from user_service.messaging.rabbitmq import RabbitMQService


@pytest.mark.asyncio
async def test_rabbitmq_connection():
    """Test RabbitMQ connection (gracefully handles connection failures)"""
    service = RabbitMQService()
    await service.connect()
    # Should not raise exception even if RabbitMQ is not running
    assert service.published_messages == []


@pytest.mark.asyncio
async def test_publish_low_stock_alert():
    """Test publishing low stock alerts"""
    service = RabbitMQService()
    await service.connect()
    
    # Publish alert
    result = await service.publish_low_stock_alert(
        inventory_item_id=1,
        product_id="test_product",
        current_quantity=5,
        threshold=10
    )
    
    assert result is True
    assert len(service.published_messages) == 1
    
    message = service.published_messages[0]
    assert message["queue"] == "low_stock_alerts"
    assert message["message"]["event_type"] == "low_stock_alert"
    assert message["message"]["current_quantity"] == 5
    assert message["message"]["threshold"] == 10
    assert message["message"]["severity"] == "warning"


@pytest.mark.asyncio
async def test_publish_stock_validation():
    """Test publishing stock validation messages"""
    service = RabbitMQService()
    await service.connect()
    
    # Publish validation
    result = await service.publish_stock_validation(
        product_id="test_product",
        requested_quantity=15,
        available_quantity=20,
        order_id="order_123"
    )
    
    assert result is True
    assert len(service.published_messages) == 1
    
    message = service.published_messages[0]
    assert message["queue"] == "stock_validation"
    assert message["message"]["event_type"] == "stock_validation"
    assert message["message"]["validation_result"] is True


@pytest.mark.asyncio
async def test_publish_inventory_update():
    """Test publishing inventory update messages"""
    service = RabbitMQService()
    await service.connect()
    
    # Publish update
    result = await service.publish_inventory_update(
        inventory_item_id=1,
        product_id="test_product",
        old_quantity=50,
        new_quantity=45,
        transaction_type="OUT"
    )
    
    assert result is True
    assert len(service.published_messages) == 1
    
    message = service.published_messages[0]
    assert message["queue"] == "inventory_updates"
    assert message["message"]["event_type"] == "inventory_update"
    assert message["message"]["quantity_change"] == -5
    assert message["message"]["transaction_type"] == "OUT"


@pytest.mark.asyncio
async def test_critical_stock_alert():
    """Test critical stock alert (zero stock)"""
    service = RabbitMQService()
    await service.connect()
    
    # Publish critical alert
    result = await service.publish_low_stock_alert(
        inventory_item_id=2,
        product_id="critical_product",
        current_quantity=0,
        threshold=10
    )
    
    assert result is True
    message = service.published_messages[0]
    assert message["message"]["severity"] == "critical"


@pytest.mark.asyncio
async def test_multiple_messages():
    """Test publishing multiple messages"""
    service = RabbitMQService()
    await service.connect()
    
    # Publish multiple messages
    await service.publish_low_stock_alert(1, "prod1", 5, 10)
    await service.publish_stock_validation("prod2", 10, 15, "order1")
    await service.publish_inventory_update(1, "prod1", 50, 45, "OUT")
    
    assert len(service.published_messages) == 3
    
    queues = [msg["queue"] for msg in service.published_messages]
    assert "low_stock_alerts" in queues
    assert "stock_validation" in queues  
    assert "inventory_updates" in queues


if __name__ == "__main__":
    pytest.main([__file__, "-v"])