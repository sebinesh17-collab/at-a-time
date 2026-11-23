-- Monitoring System Tables
-- Migration: 004_monitoring.sql

-- Metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    value FLOAT NOT NULL,
    metric_type VARCHAR(20) NOT NULL DEFAULT 'gauge',  -- counter, gauge, histogram, summary
    labels JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(name);
CREATE INDEX IF NOT EXISTS idx_metrics_labels ON metrics(labels);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);

-- Alert Rules table
CREATE TABLE IF NOT EXISTS alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    metric_name VARCHAR(200) NOT NULL,
    condition VARCHAR(10) NOT NULL,  -- >, <, >=, <=, ==, !=
    threshold FLOAT NOT NULL,
    evaluation_window_seconds INT DEFAULT 300,
    severity VARCHAR(20) NOT NULL DEFAULT 'warning',  -- info, warning, critical
    labels JSONB DEFAULT '{}',
    annotations JSONB DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT TRUE,
    last_evaluation TIMESTAMP WITH TIME ZONE,
    last_triggered TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alert_rules_metric ON alert_rules(metric_name);
CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled ON alert_rules(is_enabled) WHERE is_enabled = TRUE;

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    rule_name VARCHAR(200) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    labels JSONB DEFAULT '{}',
    annotations JSONB DEFAULT '{}',
    value FLOAT NOT NULL,
    threshold FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'firing',  -- firing, resolved, acknowledged
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_alerts_rule ON alerts(rule_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_started ON alerts(started_at);

-- Service Health table
CREATE TABLE IF NOT EXISTS service_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL,  -- healthy, degraded, unhealthy
    latency_ms INT,
    error_rate FLOAT,
    details JSONB DEFAULT '{}',
    last_check TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    uptime_percentage FLOAT DEFAULT 100.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_service_health_status ON service_health(status);

-- Dashboards table
CREATE TABLE IF NOT EXISTS dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    layout JSONB DEFAULT '[]',
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dashboards_default ON dashboards(is_default) WHERE is_default = TRUE;

-- Apply updated_at triggers
CREATE TRIGGER update_alert_rules_updated_at BEFORE UPDATE ON alert_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_service_health_updated_at BEFORE UPDATE ON service_health FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_dashboards_updated_at BEFORE UPDATE ON dashboards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();