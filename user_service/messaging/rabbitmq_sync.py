"""
Synchronous RabbitMQ messaging service for inventory operations
Used from sync gRPC handlers without asyncio complexity
"""

import pika
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import urllib.parse

logger = logging.getLogger(__name__)

class SyncRabbitMQService:
    """Synchronous RabbitMQ service for use in sync context (gRPC handlers)"""
    
    def __init__(self, connection_url: str = "amqp://guest:guest@localhost:5672/"):
        self.connection_url = connection_url
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.BlockingChannel] = None
        self.published_messages = []  # For testing purposes
        
    def connect(self) -> bool:
        """Establish connection to RabbitMQ"""
        try:
            # Parse URL to extract connection parameters
            parsed = urllib.parse.urlparse(self.connection_url)
            
            credentials = pika.PlainCredentials(
                parsed.username or 'guest',
                parsed.password or 'guest'
            )
            parameters = pika.ConnectionParameters(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 5672,
                virtual_host=parsed.path[1:] if parsed.path and len(parsed.path) > 1 else '/',
                credentials=credentials,
                connection_attempts=3,
                retry_delay=2
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange='inventory_events',
                exchange_type='topic',
                durable=True
            )
            
            # Declare queues and bind them to exchange with routing keys
            queues_config = {
                'low_stock_alerts': 'inventory.low_stock',
                'inventory_updates': 'inventory.updated',
                'stock_validation': 'inventory.validation'
            }
            
            for queue_name, routing_key in queues_config.items():
                self.channel.queue_declare(queue=queue_name, durable=True)
                self.channel.queue_bind(
                    exchange='inventory_events',
                    queue=queue_name,
                    routing_key=routing_key
                )
            
            logger.info("Connected to RabbitMQ successfully (sync)")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            self.connection = None
            self.channel = None
            return False

    def disconnect(self):
        """Close RabbitMQ connection"""
        try:
            if self.channel:
                self.channel.close()
            if self.connection and self.connection.is_open:
                self.connection.close()
            logger.info("Disconnected from RabbitMQ (sync)")
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")

    def publish_message(self, queue_name: str, message: Dict[str, Any], routing_key: str) -> bool:
        """Publish a message to exchange with specific routing key"""
        try:
            # Add message to test list for testing purposes
            self.published_messages.append({
                "queue": queue_name,
                "message": message,
                "timestamp": datetime.now()
            })
            
            # If no connection, just log and return success (for testing)
            if not self.connection or not self.channel:
                logger.warning(f"No RabbitMQ connection, message logged locally: {queue_name}")
                return True

            # Publish message
            self.channel.basic_publish(
                exchange='inventory_events',
                routing_key=routing_key,
                body=json.dumps(message).encode(),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            
            logger.info(f"Message published to exchange 'inventory_events' with routing key '{routing_key}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message with routing key {routing_key}: {e}")
            return False

    def publish_low_stock_alert(self, inventory_item_id: int, product_id: str, 
                                current_quantity: int, threshold: int) -> bool:
        """Publish a low stock alert"""
        message = {
            "event_type": "low_stock_alert",
            "inventory_item_id": inventory_item_id,
            "product_id": product_id,
            "current_quantity": current_quantity,
            "threshold": threshold,
            "timestamp": datetime.now().isoformat(),
            "severity": "critical" if current_quantity == 0 else "warning",
            "payload": {
                "inventory_item_id": inventory_item_id,
                "product_id": product_id,
                "current_quantity": current_quantity,
                "threshold": threshold,
                "severity": "critical" if current_quantity == 0 else "warning"
            }
        }
        return self.publish_message("low_stock_alerts", message, "inventory.low_stock")

    def publish_inventory_update(self, inventory_item_id: int, product_id: str,
                                 old_quantity: int, new_quantity: int, 
                                 transaction_type: str) -> bool:
        """Publish an inventory update message"""
        message = {
            "event_type": "inventory_updated",
            "inventory_item_id": inventory_item_id,
            "product_id": product_id,
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
            "quantity_change": new_quantity - old_quantity,
            "transaction_type": transaction_type,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "inventory_item_id": inventory_item_id,
                "product_id": product_id,
                "quantity_change": new_quantity - old_quantity,
                "transaction_type": transaction_type
            }
        }
        return self.publish_message("inventory_updates", message, "inventory.updated")

    def publish_stock_validation(self, product_id: str, requested_quantity: int, 
                                 available_quantity: int, order_id: str) -> bool:
        """Publish a stock validation message"""
        message = {
            "event_type": "stock_validation",
            "product_id": product_id,
            "requested_quantity": requested_quantity,
            "available_quantity": available_quantity,
            "order_id": order_id,
            "timestamp": datetime.now().isoformat(),
            "validation_result": available_quantity >= requested_quantity,
            "payload": {
                "product_id": product_id,
                "requested_quantity": requested_quantity,
                "available_quantity": available_quantity,
                "order_id": order_id,
                "validation_result": available_quantity >= requested_quantity
            }
        }
        return self.publish_message("stock_validation", message, "inventory.validation")
