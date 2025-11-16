"""
Inventory Service - Pure gRPC Server
Implements gRPC services for inventory management.
All communication via gRPC on port 50051
"""

import logging
import os
from concurrent import futures

import grpc

# Import generated gRPC stubs - compiled during Docker build
import inventory_pb2
import inventory_pb2_grpc

# Import Synchronous RabbitMQ service
from messaging.rabbitmq_sync import SyncRabbitMQService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "50"))
ENABLE_AUTO_ALERTS = os.getenv("ENABLE_AUTO_ALERTS", "true").lower() == "true"

# Initialize RabbitMQ service (synchronous version)
rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
messaging_service = SyncRabbitMQService(rabbitmq_url)

# Mock inventory database
inventory_db = {
    1: {"id": 1, "product_id": "PROD001", "quantity": 100, "location": "warehouse_a", "reserved_quantity": 10},
    2: {"id": 2, "product_id": "PROD002", "quantity": 50, "location": "warehouse_b", "reserved_quantity": 5},
}



class InventoryServicer(inventory_pb2_grpc.InventoryServiceServicer):
    """gRPC Inventory Service Implementation"""
    
    def GetInventory(self, request, context):
        """Get inventory item by product ID"""
        logger.info(f"gRPC: GetInventory for {request.product_id}")
        try:
            for item in inventory_db.values():
                if item["product_id"] == request.product_id:
                    return inventory_pb2.InventoryItem(
                        id=item["id"],
                        product_id=item["product_id"],
                        quantity=item["quantity"],
                        location=item["location"],
                        reserved_quantity=item["reserved_quantity"],
                    )
            context.abort(grpc.StatusCode.NOT_FOUND, f"Product {request.product_id} not found")
        except Exception as e:
            logger.error(f"GetInventory error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def ListInventory(self, request, context):
        """List all inventory items with pagination"""
        logger.info(f"gRPC: ListInventory limit={request.limit}, offset={request.offset}")
        try:
            limit = request.limit or 10
            offset = request.offset or 0
            
            items_list = list(inventory_db.values())
            total = len(items_list)
            paginated = items_list[offset:offset + limit]
            
            pb_items = [
                inventory_pb2.InventoryItem(
                    id=item["id"],
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    location=item["location"],
                    reserved_quantity=item["reserved_quantity"],
                )
                for item in paginated
            ]
            
            return inventory_pb2.ListInventoryResponse(items=pb_items, total=total)
        except Exception as e:
            logger.error(f"ListInventory error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def CreateInventory(self, request, context):
        """Create new inventory item"""
        logger.info(f"gRPC: CreateInventory {request.product_id}")
        try:
            new_id = max(inventory_db.keys()) + 1 if inventory_db else 1
            new_item = {
                "id": new_id,
                "product_id": request.product_id,
                "quantity": request.quantity,
                "location": request.location,
                "reserved_quantity": request.reserved_quantity,
            }
            inventory_db[new_id] = new_item
            logger.info(f"Created inventory item {new_id}")
            return inventory_pb2.InventoryItem(
                id=new_item["id"],
                product_id=new_item["product_id"],
                quantity=new_item["quantity"],
                location=new_item["location"],
                reserved_quantity=new_item["reserved_quantity"],
            )
        except Exception as e:
            logger.error(f"CreateInventory error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def UpdateInventory(self, request, context):
        """Update inventory item with low stock alert support"""
        logger.info(f"gRPC: UpdateInventory id={request.id}")
        try:
            if request.id not in inventory_db:
                context.abort(grpc.StatusCode.NOT_FOUND, f"Item {request.id} not found")
            
            item = inventory_db[request.id]
            old_quantity = item["quantity"]
            
            # Update item fields
            if request.quantity >= 0:
                item["quantity"] = request.quantity
            if request.location:
                item["location"] = request.location
            if request.reserved_quantity >= 0:
                item["reserved_quantity"] = request.reserved_quantity
            
            # Check for low stock and publish alert if needed
            new_quantity = item["quantity"]
            if ENABLE_AUTO_ALERTS and new_quantity <= LOW_STOCK_THRESHOLD:
                # Only publish alert if stock just fell below threshold
                if old_quantity > LOW_STOCK_THRESHOLD or old_quantity > new_quantity:
                    try:
                        # Publish low stock alert to RabbitMQ synchronously
                        messaging_service.publish_low_stock_alert(
                            inventory_item_id=item["id"],
                            product_id=item["product_id"],
                            current_quantity=new_quantity,
                            threshold=LOW_STOCK_THRESHOLD
                        )
                        
                        logger.warning(
                            f"LOW STOCK ALERT: Product {item['product_id']} "
                            f"has {new_quantity} units (threshold: {LOW_STOCK_THRESHOLD})"
                        )
                    except Exception as e:
                        logger.error(f"Failed to publish low stock alert: {e}")
            
            # Publish inventory update event
            if old_quantity != new_quantity:
                try:
                    messaging_service.publish_inventory_update(
                        inventory_item_id=item["id"],
                        product_id=item["product_id"],
                        old_quantity=old_quantity,
                        new_quantity=new_quantity,
                        transaction_type="UPDATE"
                    )
                except Exception as e:
                    logger.error(f"Failed to publish inventory update: {e}")
            
            logger.info(f"Updated inventory item {request.id}: {old_quantity} -> {new_quantity}")
            return inventory_pb2.InventoryItem(
                id=item["id"],
                product_id=item["product_id"],
                quantity=item["quantity"],
                location=item["location"],
                reserved_quantity=item["reserved_quantity"],
            )
        except Exception as e:
            logger.error(f"UpdateInventory error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def DeleteInventory(self, request, context):
        """Delete inventory item"""
        logger.info(f"gRPC: DeleteInventory id={request.id}")
        try:
            if request.id not in inventory_db:
                context.abort(grpc.StatusCode.NOT_FOUND, f"Item {request.id} not found")
            del inventory_db[request.id]
            logger.info(f"Deleted inventory item {request.id}")
            return inventory_pb2.Empty()
        except Exception as e:
            logger.error(f"DeleteInventory error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def CheckStock(self, request, context):
        """Check stock availability"""
        logger.info(f"gRPC: CheckStock {request.product_id} qty={request.requested_quantity}")
        try:
            for item in inventory_db.values():
                if item["product_id"] == request.product_id:
                    available_stock = item["quantity"] - item["reserved_quantity"]
                    is_available = available_stock >= request.requested_quantity
                    return inventory_pb2.StockCheckResponse(
                        available=is_available,
                        current_stock=item["quantity"],
                        available_stock=available_stock,
                        requested_quantity=request.requested_quantity,
                    )
            context.abort(grpc.StatusCode.NOT_FOUND, f"Product {request.product_id} not found")
        except Exception as e:
            logger.error(f"CheckStock error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def ReserveStock(self, request, context):
        """Reserve stock for order"""
        logger.info(f"gRPC: ReserveStock {request.product_id} qty={request.quantity} ref={request.reference_id}")
        try:
            for item in inventory_db.values():
                if item["product_id"] == request.product_id:
                    available = item["quantity"] - item["reserved_quantity"]
                    if available >= request.quantity:
                        item["reserved_quantity"] += request.quantity
                        logger.info(f"Reserved {request.quantity} units for {request.reference_id}")
                        return inventory_pb2.StockReserveResponse(
                            success=True,
                            message=f"Reserved {request.quantity} units for {request.reference_id}"
                        )
                    else:
                        return inventory_pb2.StockReserveResponse(
                            success=False,
                            message=f"Insufficient stock. Available: {available}"
                        )
            return inventory_pb2.StockReserveResponse(
                success=False,
                message=f"Product {request.product_id} not found"
            )
        except Exception as e:
            logger.error(f"ReserveStock error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def ReleaseStock(self, request, context):
        """Release reserved stock"""
        logger.info(f"gRPC: ReleaseStock {request.product_id} qty={request.quantity} ref={request.reference_id}")
        try:
            for item in inventory_db.values():
                if item["product_id"] == request.product_id:
                    if item["reserved_quantity"] >= request.quantity:
                        item["reserved_quantity"] -= request.quantity
                        logger.info(f"Released {request.quantity} units from {request.reference_id}")
                        return inventory_pb2.StockReserveResponse(
                            success=True,
                            message=f"Released {request.quantity} units from {request.reference_id}"
                        )
                    else:
                        return inventory_pb2.StockReserveResponse(
                            success=False,
                            message=f"Cannot release more than reserved ({item['reserved_quantity']})"
                        )
            return inventory_pb2.StockReserveResponse(
                success=False,
                message=f"Product {request.product_id} not found"
            )
        except Exception as e:
            logger.error(f"ReleaseStock error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))


def serve():
    """Start gRPC server on port 50051"""
    try:
        # Connect to RabbitMQ synchronously
        logger.info(f"Connecting to RabbitMQ at {rabbitmq_url}")
        if messaging_service.connect():
            logger.info(f"RabbitMQ connection established (sync). Alerts enabled: {ENABLE_AUTO_ALERTS}, Threshold: {LOW_STOCK_THRESHOLD}")
        else:
            logger.error("Failed to connect to RabbitMQ on startup")
            # Continue anyway for graceful degradation
        
        # Start gRPC server
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        inventory_pb2_grpc.add_InventoryServiceServicer_to_server(InventoryServicer(), server)
        server.add_insecure_port("[::]:50051")
        logger.info("gRPC Inventory Service starting on [::]:50051")
        server.start()
        logger.info("gRPC Inventory Service started successfully")
        server.wait_for_termination()
    except Exception as e:
        logger.error(f"Failed to start gRPC server: {e}")
        raise
    finally:
        # Cleanup RabbitMQ connection
        try:
            messaging_service.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")


if __name__ == "__main__":
    serve()