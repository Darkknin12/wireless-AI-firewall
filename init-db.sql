-- AI-Firewall Database Schema
-- PostgreSQL initialization script

-- Create blocked_ips table
CREATE TABLE IF NOT EXISTS blocked_ips (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    blocked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    unblocked_at TIMESTAMP,
    reason TEXT,
    threat_score DECIMAL(5,3),
    threat_type VARCHAR(50),
    auto_blocked BOOLEAN DEFAULT TRUE,
    duration_hours INTEGER DEFAULT 24,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(ip_address, blocked_at)
);

-- Create predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    source_ip VARCHAR(45),
    destination_ip VARCHAR(45),
    destination_port INTEGER,
    protocol VARCHAR(10),
    prediction VARCHAR(20) NOT NULL,
    xgb_score DECIMAL(5,3),
    if_score DECIMAL(5,3),
    ensemble_score DECIMAL(5,3) NOT NULL,
    was_blocked BOOLEAN DEFAULT FALSE,
    flow_duration DECIMAL(10,3),
    total_packets INTEGER,
    total_bytes BIGINT
);

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    source_ip VARCHAR(45),
    message TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(100)
);

-- Create firewall_rules table
CREATE TABLE IF NOT EXISTS firewall_rules (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    rule_type VARCHAR(20) NOT NULL,
    ip_address VARCHAR(45),
    port INTEGER,
    protocol VARCHAR(10),
    action VARCHAR(20) NOT NULL,
    reason TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_blocked_ips_ip ON blocked_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_blocked_ips_active ON blocked_ips(is_active);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp);
CREATE INDEX IF NOT EXISTS idx_predictions_source_ip ON predictions(source_ip);
CREATE INDEX IF NOT EXISTS idx_predictions_score ON predictions(ensemble_score);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type);

-- Create views
CREATE OR REPLACE VIEW active_blocks AS
SELECT 
    ip_address,
    blocked_at,
    reason,
    threat_score,
    threat_type,
    duration_hours,
    (blocked_at + (duration_hours || ' hours')::INTERVAL) AS expires_at
FROM blocked_ips
WHERE is_active = TRUE
AND (unblocked_at IS NULL OR unblocked_at > NOW());

CREATE OR REPLACE VIEW threat_summary AS
SELECT 
    DATE(timestamp) as date,
    prediction,
    COUNT(*) as count,
    AVG(ensemble_score) as avg_score,
    MAX(ensemble_score) as max_score,
    SUM(CASE WHEN was_blocked THEN 1 ELSE 0 END) as blocked_count
FROM predictions
GROUP BY DATE(timestamp), prediction
ORDER BY date DESC, count DESC;

-- Insert sample data for testing
INSERT INTO alerts (alert_type, severity, source_ip, message) VALUES
('threat_detected', 'high', '192.168.1.100', 'High threat score detected'),
('system_startup', 'info', NULL, 'AI-Firewall system started');

COMMENT ON TABLE blocked_ips IS 'Tracks all blocked IP addresses';
COMMENT ON TABLE predictions IS 'Stores all AI predictions and flow data';
COMMENT ON TABLE alerts IS 'System and security alerts';
COMMENT ON TABLE firewall_rules IS 'Active firewall rules';
