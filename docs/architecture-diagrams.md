# 🏗️ Censudx Inventory Service - Architecture Diagrams

## 📊 System Architecture Overview

```plantuml
@startuml system-architecture
!theme plain
skinparam backgroundColor #FFFFFF
skinparam handwritten false
skinparam shadowing false

title Censudx Inventory Service - System Architecture

actor "Client" as client
rectangle "API Gateway (Nginx)" as gateway {
  note right : Load Balancing\nRate Limiting\nSecurity Headers\nCORS
}

rectangle "Inventory Service" as service {
  component "FastAPI Application" as api
  component "Authentication Middleware" as auth
  component "Business Logic Layer" as logic
  component "Data Access Layer (CRUD)" as dal
  
  api --> auth : validates
  auth --> logic : processes
  logic --> dal : accesses
}

database "PostgreSQL" as db {
  entity "inventory_items" as items
  entity "inventory_transactions" as transactions  
  entity "low_stock_alerts" as alerts
}

queue "RabbitMQ" as mq {
  queue "low_stock_alerts" as lsa_queue
  queue "stock_validation" as sv_queue
  queue "inventory_updates" as iu_queue
}

cache "Redis Cache" as cache {
  note right : Session Storage\nQuery Caching\nRate Limiting
}

cloud "External Services" as external {
  service "Auth Service" as auth_svc
  service "Product Service" as prod_svc
}

' Connections
client --> gateway : HTTP/HTTPS
gateway --> api : proxies to
dal --> db : SQL queries
logic --> mq : publishes events
service --> cache : caches data
service --> external : integrates with

' Data relationships
items ||--o{ transactions : has many
items ||--o{ alerts : generates

@enduml
```

## 🔄 Request Flow Diagram

```plantuml
@startuml request-flow
!theme plain
skinparam backgroundColor #FFFFFF

title Inventory Service - Request Processing Flow

actor Client as client
participant "Nginx\nAPI Gateway" as nginx
participant "FastAPI\nApplication" as app
participant "Auth\nMiddleware" as auth
participant "Business\nLogic" as logic
participant "CRUD\nOperations" as crud
participant "PostgreSQL\nDatabase" as db
participant "RabbitMQ\nMessaging" as mq

client -> nginx : HTTP Request
nginx -> nginx : Rate Limiting\nSecurity Headers
nginx -> app : Forward Request

app -> auth : Validate Token
auth -> auth : JWT Verification
auth -> app : User Context

app -> logic : Process Business Logic
logic -> crud : Data Operations
crud -> db : SQL Query
db -> crud : Query Results
crud -> logic : Data Response

alt Low Stock Detected
  logic -> mq : Publish Alert
  mq -> mq : Queue Message
end

logic -> app : Business Response
app -> nginx : HTTP Response
nginx -> client : Final Response

@enduml
```

## 🏛️ Layered Architecture Pattern

```plantuml
@startuml layered-architecture
!theme plain
skinparam backgroundColor #FFFFFF

title Censudx Inventory Service - Layered Architecture

package "Presentation Layer" {
  [FastAPI Endpoints] as endpoints
  [Authentication Middleware] as auth_mid
  [Request/Response Models] as models
}

package "Business Logic Layer" {
  [Inventory Service] as inv_service
  [Stock Management] as stock_mgmt
  [Alert Generator] as alerter
  [Event Publisher] as publisher
}

package "Data Access Layer" {
  [CRUD Operations] as crud
  [Database Models] as db_models
  [Repository Pattern] as repository
}

package "Infrastructure Layer" {
  [PostgreSQL Driver] as pg_driver
  [RabbitMQ Client] as mq_client
  [Redis Client] as redis_client
  [External API Clients] as ext_clients
}

' Dependencies (top-down only)
endpoints --> inv_service
auth_mid --> inv_service
models --> inv_service

inv_service --> crud
stock_mgmt --> crud
alerter --> publisher
publisher --> crud

crud --> db_models
repository --> db_models

db_models --> pg_driver
publisher --> mq_client
crud --> redis_client
inv_service --> ext_clients

note right of endpoints : HTTP/REST Interface\nValidation & Serialization
note right of inv_service : Core Business Rules\nDomain Logic
note right of crud : Data Persistence\nQuery Optimization  
note right of pg_driver : Database Connectivity\nExternal Dependencies

@enduml
```

## 🎯 Design Patterns Implementation

```plantuml
@startuml design-patterns
!theme plain
skinparam backgroundColor #FFFFFF

title Design Patterns in Censudx Inventory Service

package "Repository Pattern" {
  interface IInventoryRepository {
    +get_all(): List[InventoryItem]
    +get_by_id(id): InventoryItem
    +create(item): InventoryItem
    +update(id, item): InventoryItem
    +delete(id): bool
  }
  
  class SQLInventoryRepository {
    -db_session: Session
    +get_all(): List[InventoryItem]
    +get_by_id(id): InventoryItem
    +create(item): InventoryItem
    +update(id, item): InventoryItem
    +delete(id): bool
  }
  
  IInventoryRepository <|-- SQLInventoryRepository
}

package "Dependency Injection" {
  class InventoryService {
    -repository: IInventoryRepository
    -messaging: IMessagingService
    -auth: IAuthService
    +__init__(repo, messaging, auth)
    +process_inventory_request()
  }
  
  interface IMessagingService
  interface IAuthService
  
  InventoryService --> IInventoryRepository
  InventoryService --> IMessagingService
  InventoryService --> IAuthService
}

package "Observer Pattern" {
  interface IStockObserver {
    +on_stock_changed(item, old_qty, new_qty)
  }
  
  class StockAlertObserver {
    +on_stock_changed(item, old_qty, new_qty)
  }
  
  class StockEventPublisher {
    +on_stock_changed(item, old_qty, new_qty)
  }
  
  class InventoryManager {
    -observers: List[IStockObserver]
    +add_observer(observer)
    +notify_observers(item, old_qty, new_qty)
    +update_stock(item_id, quantity)
  }
  
  IStockObserver <|-- StockAlertObserver
  IStockObserver <|-- StockEventPublisher
  InventoryManager --> IStockObserver
}

package "Factory Pattern" {
  interface IAlertFactory {
    +create_alert(type, data): Alert
  }
  
  class LowStockAlertFactory {
    +create_alert(type, data): LowStockAlert
  }
  
  class CriticalStockAlertFactory {
    +create_alert(type, data): CriticalStockAlert
  }
  
  IAlertFactory <|-- LowStockAlertFactory
  IAlertFactory <|-- CriticalStockAlertFactory
}

@enduml
```

## 🔌 Event-Driven Architecture

```plantuml
@startuml event-driven
!theme plain
skinparam backgroundColor #FFFFFF

title Event-Driven Architecture - RabbitMQ Integration

participant "Inventory Service" as service
participant "RabbitMQ Exchange" as exchange
queue "low_stock_alerts" as lsa_queue
queue "stock_validation" as sv_queue  
queue "inventory_updates" as iu_queue
participant "Alert Service" as alert_svc
participant "Order Service" as order_svc
participant "Analytics Service" as analytics_svc

== Stock Update Event ==
service -> exchange : publish(inventory_update)
exchange -> iu_queue : route message
iu_queue -> analytics_svc : consume event
analytics_svc -> analytics_svc : update metrics

== Low Stock Detection ==
service -> service : detect low stock
service -> exchange : publish(low_stock_alert)
exchange -> lsa_queue : route message
lsa_queue -> alert_svc : consume event
alert_svc -> alert_svc : send notification

== Stock Validation ==
order_svc -> exchange : publish(stock_validation_request)
exchange -> sv_queue : route message  
sv_queue -> service : consume request
service -> service : validate stock
service -> exchange : publish(stock_validation_response)
exchange -> order_svc : delivery response

note over exchange : Event Routing\nMessage Persistence\nReliable Delivery

@enduml
```

## 🗄️ Database Schema Diagram

```plantuml
@startuml database-schema
!theme plain
skinparam backgroundColor #FFFFFF

title Database Schema - Entity Relationship Diagram

entity "inventory_items" {
  * **id** : SERIAL (PK)
  --
  * product_id : VARCHAR(255) UNIQUE
  * quantity : INTEGER ≥ 0
  * reserved_quantity : INTEGER ≥ 0
  * location : VARCHAR(255)
  * created_at : TIMESTAMP
  * updated_at : TIMESTAMP
  --
  CONSTRAINT: reserved_quantity ≤ quantity
}

entity "inventory_transactions" {
  * **id** : SERIAL (PK)
  --
  * inventory_item_id : INTEGER (FK)
  * transaction_type : ENUM('IN','OUT','RESERVED','RELEASED')
  * quantity : INTEGER > 0
  * reference_id : VARCHAR(255)
  * notes : TEXT
  * created_at : TIMESTAMP
}

entity "low_stock_alerts" {
  * **id** : SERIAL (PK)
  --
  * inventory_item_id : INTEGER (FK)
  * threshold : INTEGER ≥ 0
  * current_quantity : INTEGER ≥ 0
  * is_resolved : BOOLEAN
  * created_at : TIMESTAMP
  * resolved_at : TIMESTAMP (nullable)
}

' Relationships
inventory_items ||--o{ inventory_transactions : "has many"
inventory_items ||--o{ low_stock_alerts : "generates"

' Indexes
note right of inventory_items : **Indexes:**\n• product_id (UNIQUE)\n• location\n• quantity\n• updated_at

note right of inventory_transactions : **Indexes:**\n• inventory_item_id\n• transaction_type\n• created_at\n• reference_id

note right of low_stock_alerts : **Indexes:**\n• inventory_item_id\n• is_resolved\n• created_at

@enduml
```

## 🔒 Security Architecture

```plantuml
@startuml security-architecture
!theme plain
skinparam backgroundColor #FFFFFF

title Security Architecture & Authentication Flow

actor "Client" as client
participant "Nginx\n(Rate Limiting)" as nginx
participant "FastAPI\n(Auth Middleware)" as api
participant "JWT Validator" as jwt
participant "Auth Service" as auth_svc
participant "Protected Resource" as resource

client -> nginx : Request + JWT Token
nginx -> nginx : Rate Limit Check
nginx -> api : Forward if within limits

api -> jwt : Extract & Validate JWT
jwt -> jwt : Verify Signature\nCheck Expiration\nValidate Claims

alt Valid Token
  jwt -> auth_svc : Verify User Permissions
  auth_svc -> jwt : User Context + Roles
  jwt -> api : Authentication Success
  api -> resource : Process Request
  resource -> api : Response
  api -> client : Success Response
else Invalid Token
  jwt -> api : Authentication Failed
  api -> client : 401 Unauthorized
end

note over nginx : **Security Features:**\n• Rate Limiting (10 req/s)\n• Security Headers\n• CORS Configuration\n• DDoS Protection

note over jwt : **JWT Validation:**\n• Signature Verification\n• Expiration Checking\n• Issuer Validation\n• Role-Based Access Control

@enduml
```

## 🚀 Deployment Architecture

```plantuml
@startuml deployment-architecture
!theme plain
skinparam backgroundColor #FFFFFF

title Deployment Architecture (Docker + Render)

node "Docker Container Network" {
  node "nginx-gateway" {
    component "Nginx" as nginx
    port "80" as port80
    port "443" as port443
  }
  
  node "inventory-service" {
    component "FastAPI App" as app
    component "Uvicorn Server" as uvicorn
    port "8000" as port8000
  }
  
  node "postgres-db" {
    database "PostgreSQL 15" as db
    port "5432" as port5432
  }
  
  node "rabbitmq-broker" {
    queue "RabbitMQ" as mq
    port "5672" as port5672
    port "15672" as mgmt_port
  }
  
  node "redis-cache" {
    storage "Redis" as cache
    port "6379" as port6379
  }
}

cloud "Render Platform" {
  service "Web Service" as web_svc
  service "PostgreSQL Service" as db_svc
  service "Redis Service" as cache_svc
}

actor "Users" as users
cloud "GitHub Actions" as ci

' Connections
users --> port80
users --> port443
nginx --> app : proxy_pass
app --> db : SQL connection
app --> mq : AMQP connection
app --> cache : Redis connection

' CI/CD
ci -> web_svc : Deploy
ci -> ci : Run Tests\nBuild Docker\nQuality Checks

' External services
web_svc --> db_svc : Database Connection
web_svc --> cache_svc : Cache Connection

note right of web_svc : **Auto-Deploy:**\n• GitHub Integration\n• Health Checks\n• Scaling\n• SSL/TLS

note right of ci : **CI/CD Pipeline:**\n• 18 Automated Tests\n• Multi-version Testing\n• Docker Validation\n• Quality Verification

@enduml
```