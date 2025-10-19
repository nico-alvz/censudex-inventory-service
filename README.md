# 
```
░▒█▀▀▄░█▀▀░█▀▀▄░█▀▀░█░▒█░█▀▄░█░█░░░▀█▀░█▀▀▄░▄░░░▄░█▀▀░█▀▀▄░▀█▀░▄▀▀▄░█▀▀▄░█░░█░░
░▒█░░░░█▀▀░█░▒█░▀▀▄░█░▒█░█░█░▄▀▄░░░▒█░░█░▒█░░█▄█░░█▀▀░█░▒█░░█░░█░░█░█▄▄▀░█▄▄█░░
░▒█▄▄▀░▀▀▀░▀░░▀░▀▀▀░░▀▀▀░▀▀░░▀░▀░░░▄█▄░▀░░▀░░░▀░░░▀▀▀░▀░░▀░░▀░░░▀▀░░▀░▀▀░▄▄▄▀░░

```


[![CI/CD](https://github.com/och1ai/censudx-inventory-service/actions/workflows/ci.yml/badge.svg)](https://github.com/och1ai/censudx-inventory-service/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-18%2F18-brightgreen)](https://github.com/och1ai/censudx-inventory-service/actions)
[![Quality](https://img.shields.io/badge/quality-100%25-brightgreen)](https://github.com/och1ai/censudx-inventory-service)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://github.com/och1ai/censudx-inventory-service)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://github.com/och1ai/censudx-inventory-service)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)](https://github.com/och1ai/censudx-inventory-service)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.13-orange)](https://github.com/och1ai/censudx-inventory-service)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://github.com/och1ai/censudx-inventory-service)

> 🏦 A comprehensive inventory management microservice built with FastAPI, PostgreSQL, and RabbitMQ. Provides robust inventory tracking, stock management, and automated alerting capabilities with event-driven architecture.

## 🏗️ System Architecture

![System Architecture](docs/images/system-architecture.png)

**Key Components:**
- **FastAPI Application**: High-performance async web framework with automatic OpenAPI documentation
- **Nginx API Gateway**: Load balancing, rate limiting, and security layer
- **PostgreSQL Database**: ACID-compliant relational database with optimized indexing
- **RabbitMQ Messaging**: Event-driven communication with persistent message queues
- **Redis Cache**: High-performance caching and session management

## 📖 API Documentation

### Swagger UI (OpenAPI)
- **Interactive API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative UI (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### API Endpoints Overview

| Method | Endpoint | Description | Tag |
|--------|----------|-------------|-----|
| GET | `/health` | Service health check | health |
| GET | `/api/v1/inventory/` | List all inventory items | inventory |
| POST | `/api/v1/inventory/` | Create new inventory item | inventory |
| GET | `/api/v1/inventory/{id}` | Get inventory item by ID | inventory |
| PUT | `/api/v1/inventory/{id}` | Update inventory item | inventory |
| DELETE | `/api/v1/inventory/{id}` | Delete inventory item | inventory |
| POST | `/api/v1/inventory/check-stock` | Check stock availability | stock |
| POST | `/api/v1/inventory/reserve` | Reserve stock for orders | stock |
| POST | `/api/v1/inventory/release` | Release reserved stock | stock |
| GET | `/api/v1/inventory/alerts` | Get low stock alerts | alerts |
| GET | `/api/v1/inventory/transactions/{id}` | Get transaction history | transactions |

## 🎨 Design Patterns & Architecture

This service implements several enterprise design patterns for maintainable, scalable code:

### 🏛️ **Layered Architecture Pattern**
```
┌─────────────────────────────────────┐
│        Presentation Layer          │  ← FastAPI endpoints, middleware
├─────────────────────────────────────┤
│       Business Logic Layer         │  ← Core inventory operations
├─────────────────────────────────────┤
│        Data Access Layer           │  ← CRUD operations, repositories
├─────────────────────────────────────┤
│       Infrastructure Layer         │  ← Database, messaging, external APIs
└─────────────────────────────────────┘
```

### 🔧 **Implemented Patterns**

#### **1. Repository Pattern**
Abstracts data access logic for clean separation of concerns:

```python path=null start=null
# Abstract base repository
from abc import ABC, abstractmethod
from typing import List, Optional

class IInventoryRepository(ABC):
    @abstractmethod
    async def get_all(self) -> List[InventoryItem]:
        pass
    
    @abstractmethod
    async def get_by_id(self, item_id: int) -> Optional[InventoryItem]:
        pass
    
    @abstractmethod
    async def create(self, item: InventoryItemCreate) -> InventoryItem:
        pass
    
    @abstractmethod
    async def update(self, item_id: int, item: InventoryItemUpdate) -> InventoryItem:
        pass
    
    @abstractmethod
    async def delete(self, item_id: int) -> bool:
        pass

# Concrete implementation
class PostgresInventoryRepository(IInventoryRepository):
    def __init__(self, db_session):
        self.db = db_session
    
    async def get_all(self) -> List[InventoryItem]:
        query = "SELECT * FROM inventory_items ORDER BY created_at DESC"
        result = await self.db.execute(query)
        return [InventoryItem(**row) for row in result.fetchall()]
    
    async def get_by_id(self, item_id: int) -> Optional[InventoryItem]:
        query = "SELECT * FROM inventory_items WHERE id = :id"
        result = await self.db.execute(query, {"id": item_id})
        row = result.fetchone()
        return InventoryItem(**row) if row else None
    
    async def create(self, item: InventoryItemCreate) -> InventoryItem:
        query = """
        INSERT INTO inventory_items (product_id, quantity, location, reserved_quantity)
        VALUES (:product_id, :quantity, :location, :reserved_quantity)
        RETURNING *
        """
        result = await self.db.execute(query, item.dict())
        row = result.fetchone()
        return InventoryItem(**row)
```

#### **2. Dependency Injection Pattern**
Leverages FastAPI's built-in DI system for loose coupling:

```python path=null start=null
# Dependency providers
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_database_session() -> AsyncSession:
    """Database session dependency"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_inventory_repository(
    db: AsyncSession = Depends(get_database_session)
) -> IInventoryRepository:
    """Repository dependency injection"""
    return PostgresInventoryRepository(db)

def get_messaging_service() -> RabbitMQService:
    """Messaging service dependency"""
    return messaging_service

# Usage in endpoints
@app.post("/api/v1/inventory/", response_model=InventoryItemResponse)
async def create_inventory_item(
    item: InventoryItemCreate,
    repository: IInventoryRepository = Depends(get_inventory_repository),
    messaging: RabbitMQService = Depends(get_messaging_service)
):
    """Create inventory item with injected dependencies"""
    new_item = await repository.create(item)
    await messaging.publish_inventory_update(
        new_item.id, new_item.product_id, 0, new_item.quantity, "IN"
    )
    return new_item
```

#### **3. Observer Pattern**
Stock level monitoring and automated alerting:

```python path=null start=null
# Observer interface
from abc import ABC, abstractmethod
from typing import List

class StockObserver(ABC):
    @abstractmethod
    async def on_stock_changed(self, item: InventoryItem, old_quantity: int):
        pass

# Concrete observers
class LowStockAlertObserver(StockObserver):
    def __init__(self, messaging_service: RabbitMQService, threshold: int = 10):
        self.messaging = messaging_service
        self.threshold = threshold
    
    async def on_stock_changed(self, item: InventoryItem, old_quantity: int):
        """Trigger alert when stock falls below threshold"""
        if item.quantity <= self.threshold and old_quantity > self.threshold:
            await self.messaging.publish_low_stock_alert(
                item.id, item.product_id, item.quantity, self.threshold
            )

class InventoryAuditObserver(StockObserver):
    def __init__(self, repository: IInventoryRepository):
        self.repository = repository
    
    async def on_stock_changed(self, item: InventoryItem, old_quantity: int):
        """Log all stock changes for audit trail"""
        transaction = InventoryTransaction(
            inventory_item_id=item.id,
            transaction_type="IN" if item.quantity > old_quantity else "OUT",
            quantity=abs(item.quantity - old_quantity),
            reference_id=f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        await self.repository.create_transaction(transaction)

# Subject (observable) class
class StockManager:
    def __init__(self):
        self._observers: List[StockObserver] = []
    
    def add_observer(self, observer: StockObserver):
        self._observers.append(observer)
    
    def remove_observer(self, observer: StockObserver):
        self._observers.remove(observer)
    
    async def _notify_observers(self, item: InventoryItem, old_quantity: int):
        for observer in self._observers:
            await observer.on_stock_changed(item, old_quantity)
    
    async def update_stock(self, item: InventoryItem, new_quantity: int):
        old_quantity = item.quantity
        item.quantity = new_quantity
        await self._notify_observers(item, old_quantity)
```

#### **4. Factory Pattern**
Alert and message creation with consistent structure:

```python path=null start=null
# Alert factory
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Alert:
    id: str
    type: str
    severity: AlertSeverity
    message: str
    metadata: dict
    timestamp: datetime

class AlertFactory:
    """Factory for creating different types of alerts"""
    
    @staticmethod
    def create_low_stock_alert(item: InventoryItem, threshold: int) -> Alert:
        severity = AlertSeverity.CRITICAL if item.quantity == 0 else AlertSeverity.WARNING
        
        return Alert(
            id=f"low_stock_{item.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type="low_stock",
            severity=severity,
            message=f"Product {item.product_id} has {item.quantity} units remaining (threshold: {threshold})",
            metadata={
                "inventory_item_id": item.id,
                "product_id": item.product_id,
                "current_quantity": item.quantity,
                "threshold": threshold,
                "location": item.location
            },
            timestamp=datetime.now()
        )
    
    @staticmethod
    def create_stock_validation_alert(product_id: str, requested: int, available: int) -> Alert:
        is_sufficient = available >= requested
        severity = AlertSeverity.INFO if is_sufficient else AlertSeverity.WARNING
        
        return Alert(
            id=f"stock_validation_{product_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type="stock_validation",
            severity=severity,
            message=f"Stock validation for {product_id}: {requested} requested, {available} available",
            metadata={
                "product_id": product_id,
                "requested_quantity": requested,
                "available_quantity": available,
                "validation_result": is_sufficient
            },
            timestamp=datetime.now()
        )

# Message factory for RabbitMQ
class MessageFactory:
    """Factory for creating standardized messages"""
    
    @staticmethod
    def create_inventory_event(event_type: str, payload: dict) -> dict:
        return {
            "event_id": f"{event_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "service": "inventory-service",
            "version": "1.0.0",
            "payload": payload
        }
    
    @staticmethod
    def create_stock_update_message(item: InventoryItem, old_qty: int, transaction_type: str) -> dict:
        return MessageFactory.create_inventory_event("stock_updated", {
            "inventory_item_id": item.id,
            "product_id": item.product_id,
            "old_quantity": old_qty,
            "new_quantity": item.quantity,
            "quantity_change": item.quantity - old_qty,
            "transaction_type": transaction_type,
            "location": item.location
        })
```

#### **5. Event-Driven Architecture**
Asynchronous messaging for decoupled services:

```python path=null start=null
# Event bus implementation
import asyncio
from typing import Dict, List, Callable, Any

class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._middlewares: List[Callable] = []
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to an event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def add_middleware(self, middleware: Callable):
        """Add middleware for event processing"""
        self._middlewares.append(middleware)
    
    async def publish(self, event_type: str, event_data: Any):
        """Publish an event to all subscribers"""
        # Apply middleware
        for middleware in self._middlewares:
            event_data = await middleware(event_type, event_data)
        
        # Notify handlers
        if event_type in self._handlers:
            tasks = [
                asyncio.create_task(handler(event_data))
                for handler in self._handlers[event_type]
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

# Event handlers
class InventoryEventHandlers:
    def __init__(self, messaging: RabbitMQService, alert_factory: AlertFactory):
        self.messaging = messaging
        self.alert_factory = alert_factory
    
    async def handle_stock_decreased(self, event_data: dict):
        """Handle stock decrease events"""
        item = event_data['item']
        threshold = event_data.get('threshold', 10)
        
        if item.quantity <= threshold:
            alert = self.alert_factory.create_low_stock_alert(item, threshold)
            await self.messaging.publish_low_stock_alert(
                item.id, item.product_id, item.quantity, threshold
            )
    
    async def handle_stock_reserved(self, event_data: dict):
        """Handle stock reservation events"""
        await self.messaging.publish_stock_validation(
            event_data['product_id'],
            event_data['reserved_quantity'],
            event_data['available_quantity'],
            event_data['order_id']
        )

# Usage in service layer
class InventoryService:
    def __init__(self, repository: IInventoryRepository, event_bus: EventBus):
        self.repository = repository
        self.event_bus = event_bus
    
    async def update_stock(self, item_id: int, new_quantity: int):
        item = await self.repository.get_by_id(item_id)
        old_quantity = item.quantity
        
        # Update stock
        item.quantity = new_quantity
        updated_item = await self.repository.update(item_id, item)
        
        # Publish events
        if new_quantity < old_quantity:
            await self.event_bus.publish('stock_decreased', {
                'item': updated_item,
                'old_quantity': old_quantity,
                'threshold': 10
            })
        elif new_quantity > old_quantity:
            await self.event_bus.publish('stock_increased', {
                'item': updated_item,
                'old_quantity': old_quantity
            })
        
        return updated_item
```

### 📊 **Additional Architecture Diagrams**

For detailed architecture diagrams including request flows, design patterns, database schemas, and deployment architecture, see: **[Architecture Diagrams](docs/architecture-diagrams.md)**

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- RabbitMQ 3.8+
- Docker (optional)

### Local Development

#### **Step 1: Clone and Environment Setup**
```bash
# Clone repository
git clone https://github.com/och1ai/censudx-inventory-service.git
cd censudx-inventory-service

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

#### **Step 2: Database Setup (PostgreSQL)**
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE censudx_inventory;
CREATE USER inventory_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE censudx_inventory TO inventory_user;
\q
```

#### **Step 3: Message Queue Setup (RabbitMQ)**
```bash
# Install RabbitMQ (Ubuntu/Debian)
sudo apt install rabbitmq-server

# Start RabbitMQ service
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server

# Enable management plugin
sudo rabbitmq-plugins enable rabbitmq_management

# Create RabbitMQ user (optional)
sudo rabbitmqctl add_user inventory_user your_password
sudo rabbitmqctl set_permissions -p / inventory_user ".*" ".*" ".*"
```

#### **Step 4: Environment Configuration**
```bash
# Create environment file
cp .env.example .env

# Edit .env file with your credentials
cat > .env << EOF
DATABASE_URL=postgresql://inventory_user:your_password@localhost/censudx_inventory
RABBITMQ_URL=amqp://inventory_user:your_password@localhost:5672/
SECRET_KEY=your-super-secret-key-here
LOW_STOCK_THRESHOLD=10
EOF
```

#### **Step 5: Database Initialization**
```bash
# Run database migrations (if using Alembic)
# alembic upgrade head

# Or initialize database tables directly
python -c "
from user_service.db.database import init_db
init_db()
print('Database initialized successfully')
"
```

#### **Step 6: Start the Services**

**Terminal 1 - Main Application:**
```bash
cd user_service
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Optional API Gateway (if needed):**
```bash
# If you have nginx configured
sudo nginx -t && sudo systemctl restart nginx

# Or run simple API gateway
python api_gateway.py
```

#### **Step 7: Verify Installation**
```bash
# Test API health
curl http://localhost:8000/health

# Test RabbitMQ management UI
open http://localhost:15672  # Default: guest/guest

# Run test suite
python -m pytest test_inventory_api.py test_rabbitmq_integration.py -v
```

#### **Step 8: Access Points**
- **API Swagger UI**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **RabbitMQ Management**: http://localhost:15672
- **PostgreSQL**: localhost:5432

### **Troubleshooting Common Issues**

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check RabbitMQ status
sudo systemctl status rabbitmq-server

# View application logs
tail -f /var/log/nginx/error.log  # If using nginx

# Test database connection
psql -h localhost -U inventory_user -d censudx_inventory

# Reset RabbitMQ (if needed)
sudo rabbitmqctl stop_app
sudo rabbitmqctl reset
sudo rabbitmqctl start_app
```

### Docker Deployment

```bash
# Quick start with all services
docker-compose up -d

# Or build and run manually
docker build -t censudx-inventory-service .
docker run -p 8000:8000 -e SECRET_KEY=your-secret censudx-inventory-service
```

## 🧪 Testing & Quality

### Automated Testing Suite
- **18 comprehensive tests** covering all functionality
- **API endpoint testing** with live cURL validation
- **RabbitMQ integration** testing with real broker
- **Multi-version testing** (Python 3.11, 3.12)
- **Quality verification** with 100% score

```bash
# Run all tests
pytest test_inventory_api.py test_rabbitmq_integration.py -v

# Run with coverage
pytest --cov=user_service --cov-report=html

# Quality verification
python verify_quality.py
```

### CI/CD Pipeline
The project includes a comprehensive 7-stage CI/CD pipeline:

1. **🔍 Lint** → Code quality and formatting
2. **🔒 Security** → Vulnerability scanning
3. **🧪 Unit Tests** → 18 comprehensive tests across Python versions
4. **🐳 Docker Build** → Container build and validation
5. **🎯 API Testing** → Live endpoint testing with cURL + RabbitMQ integration
6. **✅ Quality** → Overall project quality verification (100%)
7. **🚀 Deploy Check** → Deployment readiness validation

## 🐳 Docker & Deployment

### Services Included
- **Inventory Service**: FastAPI application (port 8000)
- **PostgreSQL**: Database with sample data (port 5432)
- **RabbitMQ**: Message broker with management UI (ports 5672, 15672)
- **Redis**: Caching service (port 6379)
- **Nginx**: API Gateway with security features (ports 80, 443)

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///./inventory.db` |
| `RABBITMQ_URL` | RabbitMQ connection string | `amqp://localhost` |
| `SECRET_KEY` | JWT secret key | `dev-secret-key` |
| `LOW_STOCK_THRESHOLD` | Default low stock threshold | `10` |

### Deployment Platforms
- ✅ **Render**: Configured with `render.yaml`
- ✅ **Docker**: Multi-service stack with `docker-compose.yml`
- ✅ **Manual**: Production deployment guides included

## 📊 Database Schema

The service uses three core tables with optimized relationships:

- **`inventory_items`**: Main inventory records with stock levels
- **`inventory_transactions`**: Complete audit trail of all stock movements
- **`low_stock_alerts`**: Automated alerting for inventory management

Detailed schema with relationships available in [Architecture Diagrams](docs/architecture-diagrams.md).

## 🐰 RabbitMQ Integration

### Message Queues
- **`low_stock_alerts`**: Published when inventory falls below threshold
- **`stock_validation`**: Used for order stock validation
- **`inventory_updates`**: Published on stock level changes

### Event-Driven Features
- Automated low stock notifications
- Real-time inventory updates
- Asynchronous order processing
- Decoupled service communication

## 💡 Usage Examples

### Python Client
```python
import requests

# Configuration
BASE_URL = "http://localhost:8000"
headers = {"Authorization": "Bearer your-jwt-token"}

# Create inventory item
inventory_data = {
    "product_id": "laptop-001",
    "quantity": 50,
    "location": "warehouse-main"
}

response = requests.post(
    f"{BASE_URL}/api/v1/inventory/",
    json=inventory_data,
    headers=headers
)
print(f"Created: {response.json()}")

# Check stock availability
stock_check = {
    "product_id": "laptop-001",
    "requested_quantity": 5
}

response = requests.post(
    f"{BASE_URL}/api/v1/inventory/check-stock",
    json=stock_check,
    headers=headers
)
print(f"Stock available: {response.json()['available']}")
```

### cURL Examples
```bash
# Health check
curl http://localhost:8000/health

# Create inventory item
curl -X POST "http://localhost:8000/api/v1/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "widget-001",
    "quantity": 100,
    "location": "shelf-a1"
  }'

# Check stock
curl -X POST "http://localhost:8000/api/v1/inventory/check-stock" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "widget-001",
    "requested_quantity": 10
  }'
```

## 🔧 Development

### Adding New Features
1. Create database model in `user_service/db/models.py`
2. Add Pydantic schema in `user_service/schemas/`
3. Implement CRUD operations in `user_service/crud/`
4. Create API endpoints in `user_service/api/`
5. Add comprehensive tests
6. Update Swagger documentation

### Code Standards
- **Black** for code formatting
- **isort** for import sorting
- **Type hints** for all functions
- **Comprehensive docstrings**
- **pytest** for testing

## 📊 Project Statistics

- **Lines of Code**: 2,200+
- **Test Coverage**: 18/18 tests passing
- **Quality Score**: 100%
- **API Endpoints**: 11 endpoints
- **Database Tables**: 3 optimized tables
- **Message Queues**: 3 event-driven queues
- **Docker Services**: 5 integrated services

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Repository**: [GitHub](https://github.com/och1ai/censudx-inventory-service)
- **CI/CD Pipeline**: [GitHub Actions](https://github.com/och1ai/censudx-inventory-service/actions)
- **API Documentation**: [Swagger UI](http://localhost:8000/docs)
- **Architecture Diagrams**: [Detailed Diagrams](docs/architecture-diagrams.md)

---

**Built with ❤️ for efficient inventory management** | **FastAPI + PostgreSQL + RabbitMQ**
