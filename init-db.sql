-- Initialize Inventory Database
-- This script runs when PostgreSQL container starts

-- Create database if not exists
\c inventory_db;

-- Create inventory items table
CREATE TABLE IF NOT EXISTS inventory_items (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL UNIQUE,
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER NOT NULL DEFAULT 0,
    location VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT positive_quantity CHECK (quantity >= 0),
    CONSTRAINT positive_reserved CHECK (reserved_quantity >= 0),
    CONSTRAINT reserved_not_exceed_quantity CHECK (reserved_quantity <= quantity)
);

-- Create inventory transactions table
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id SERIAL PRIMARY KEY,
    inventory_item_id INTEGER NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL CHECK (transaction_type IN ('IN', 'OUT', 'RESERVED', 'RELEASED')),
    quantity INTEGER NOT NULL,
    reference_id VARCHAR(255),
    notes TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT positive_transaction_quantity CHECK (quantity > 0)
);

-- Create low stock alerts table
CREATE TABLE IF NOT EXISTS low_stock_alerts (
    id SERIAL PRIMARY KEY,
    inventory_item_id INTEGER NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
    threshold INTEGER NOT NULL,
    current_quantity INTEGER NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE NULL,
    CONSTRAINT positive_threshold CHECK (threshold >= 0),
    CONSTRAINT positive_current CHECK (current_quantity >= 0)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_inventory_items_product_id ON inventory_items(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_items_location ON inventory_items(location);
CREATE INDEX IF NOT EXISTS idx_inventory_items_quantity ON inventory_items(quantity);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_item_id ON inventory_transactions(inventory_item_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_type ON inventory_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_created ON inventory_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_low_stock_alerts_item_id ON low_stock_alerts(inventory_item_id);
CREATE INDEX IF NOT EXISTS idx_low_stock_alerts_resolved ON low_stock_alerts(is_resolved);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_inventory_items_updated_at
    BEFORE UPDATE ON inventory_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO inventory_items (product_id, quantity, reserved_quantity, location) VALUES
    ('laptop-001', 50, 5, 'warehouse-a'),
    ('laptop-002', 30, 0, 'warehouse-a'),
    ('mouse-001', 100, 10, 'warehouse-b'),
    ('keyboard-001', 75, 5, 'warehouse-b'),
    ('monitor-001', 20, 2, 'warehouse-c'),
    ('headphones-001', 8, 0, 'warehouse-c')
ON CONFLICT (product_id) DO NOTHING;

-- Insert sample transactions
INSERT INTO inventory_transactions (inventory_item_id, transaction_type, quantity, reference_id, notes) VALUES
    (1, 'IN', 50, 'purchase-001', 'Initial stock'),
    (2, 'IN', 30, 'purchase-002', 'Initial stock'),
    (3, 'IN', 100, 'purchase-003', 'Initial stock'),
    (1, 'RESERVED', 5, 'order-001', 'Reserved for customer order'),
    (3, 'RESERVED', 10, 'order-002', 'Reserved for bulk order')
ON CONFLICT DO NOTHING;

-- Insert sample low stock alerts
INSERT INTO low_stock_alerts (inventory_item_id, threshold, current_quantity, is_resolved) VALUES
    (6, 10, 8, FALSE)
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO inventory_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO inventory_user;