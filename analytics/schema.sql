-- Sentinel Analytics Database Schema
-- Business Intelligence layer for Sentinel RC1
-- Aggregated metrics, trend analysis, and reporting

-- ====================
-- DECISIONS AGGREGATED
-- ====================
-- Hourly rollups of authorization decisions
CREATE TABLE IF NOT EXISTS decisions_aggregated (
    id SERIAL PRIMARY KEY,
    aggregation_period TIMESTAMP NOT NULL,
    period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('hour', 'day')),

    -- Volume metrics
    total_decisions INTEGER NOT NULL DEFAULT 0,
    allow_count INTEGER NOT NULL DEFAULT 0,
    escalate_count INTEGER NOT NULL DEFAULT 0,
    contain_count INTEGER NOT NULL DEFAULT 0,

    -- Financial metrics
    total_value BIGINT NOT NULL DEFAULT 0,  -- in smallest currency unit (paise)
    allow_value BIGINT NOT NULL DEFAULT 0,
    escalate_value BIGINT NOT NULL DEFAULT 0,
    contain_value BIGINT NOT NULL DEFAULT 0,
    prevented_fraud_value BIGINT NOT NULL DEFAULT 0,

    -- Risk metrics
    avg_risk_score FLOAT,
    max_risk_score FLOAT,
    min_risk_score FLOAT,
    high_risk_count INTEGER NOT NULL DEFAULT 0,  -- risk >= 0.7
    medium_risk_count INTEGER NOT NULL DEFAULT 0,  -- 0.4 <= risk < 0.7
    low_risk_count INTEGER NOT NULL DEFAULT 0,  -- risk < 0.4

    -- Performance metrics
    avg_latency_ms FLOAT,
    p95_latency_ms FLOAT,
    p99_latency_ms FLOAT,
    error_count INTEGER NOT NULL DEFAULT 0,

    -- ML metrics
    fusion_disagreement_count INTEGER NOT NULL DEFAULT 0,
    avg_behavioral_risk FLOAT,
    avg_semantic_risk FLOAT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(aggregation_period, period_type)
);

CREATE INDEX idx_decisions_agg_period ON decisions_aggregated(aggregation_period DESC);
CREATE INDEX idx_decisions_agg_type ON decisions_aggregated(period_type);

-- ====================
-- AGENT METRICS
-- ====================
-- Per-agent performance and behavioral tracking
CREATE TABLE IF NOT EXISTS agent_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    aggregation_period TIMESTAMP NOT NULL,
    period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('hour', 'day')),

    -- Transaction metrics
    total_transactions INTEGER NOT NULL DEFAULT 0,
    total_value BIGINT NOT NULL DEFAULT 0,
    avg_transaction_value BIGINT NOT NULL DEFAULT 0,

    -- Decision breakdown
    allow_count INTEGER NOT NULL DEFAULT 0,
    escalate_count INTEGER NOT NULL DEFAULT 0,
    contain_count INTEGER NOT NULL DEFAULT 0,

    -- Risk profile
    avg_risk_score FLOAT,
    max_risk_score FLOAT,
    risk_trend VARCHAR(20),  -- 'increasing', 'decreasing', 'stable'

    -- Behavioral patterns
    unique_recipients INTEGER NOT NULL DEFAULT 0,
    unique_action_types INTEGER NOT NULL DEFAULT 0,
    behavioral_drift_score FLOAT,
    anomaly_count INTEGER NOT NULL DEFAULT 0,

    -- Policy compliance
    policy_violations INTEGER NOT NULL DEFAULT 0,

    -- Activity patterns
    first_transaction_time TIME,
    last_transaction_time TIME,
    peak_hour INTEGER,  -- Hour of day with most activity (0-23)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(agent_id, aggregation_period, period_type)
);

CREATE INDEX idx_agent_metrics_agent ON agent_metrics(agent_id);
CREATE INDEX idx_agent_metrics_period ON agent_metrics(aggregation_period DESC);
CREATE INDEX idx_agent_metrics_risk ON agent_metrics(avg_risk_score DESC);

-- ====================
-- FRAUD EVENTS
-- ====================
-- Detected fraud attempts and contained threats
CREATE TABLE IF NOT EXISTS fraud_events (
    id SERIAL PRIMARY KEY,
    intent_id VARCHAR(255) UNIQUE NOT NULL,
    detected_at TIMESTAMP NOT NULL,

    -- Agent information
    agent_id VARCHAR(255) NOT NULL,

    -- Transaction details
    action_type VARCHAR(50) NOT NULL,
    amount BIGINT NOT NULL,
    currency VARCHAR(3) NOT NULL,
    recipient VARCHAR(255) NOT NULL,

    -- Risk assessment
    risk_score FLOAT NOT NULL,
    behavioral_risk FLOAT,
    semantic_risk FLOAT,

    -- Detection details
    fraud_type VARCHAR(50),  -- 'velocity', 'anomaly', 'pattern', 'policy'
    detection_method VARCHAR(50),  -- 'ml', 'policy', 'manual'
    decision VARCHAR(20) NOT NULL,
    decision_reason TEXT,

    -- Impact
    prevented_loss BIGINT,  -- Estimated prevented fraud value

    -- Investigation
    investigated BOOLEAN DEFAULT FALSE,
    investigation_outcome VARCHAR(50),  -- 'confirmed_fraud', 'false_positive', 'pending'
    investigated_at TIMESTAMP,
    investigator_notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fraud_events_detected ON fraud_events(detected_at DESC);
CREATE INDEX idx_fraud_events_agent ON fraud_events(agent_id);
CREATE INDEX idx_fraud_events_type ON fraud_events(fraud_type);
CREATE INDEX idx_fraud_events_investigated ON fraud_events(investigated);

-- ====================
-- POLICY VIOLATIONS
-- ====================
-- Policy breaches and rule violations
CREATE TABLE IF NOT EXISTS policy_violations (
    id SERIAL PRIMARY KEY,
    intent_id VARCHAR(255) NOT NULL,
    violated_at TIMESTAMP NOT NULL,

    -- Policy details
    policy_rule VARCHAR(255) NOT NULL,
    violation_type VARCHAR(50) NOT NULL,  -- 'threshold', 'pattern', 'blocklist', 'velocity'
    severity VARCHAR(20) NOT NULL,  -- 'low', 'medium', 'high', 'critical'

    -- Context
    agent_id VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    amount BIGINT NOT NULL,

    -- Resolution
    action_taken VARCHAR(50) NOT NULL,  -- 'blocked', 'escalated', 'allowed_with_warning'
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_policy_violations_time ON policy_violations(violated_at DESC);
CREATE INDEX idx_policy_violations_agent ON policy_violations(agent_id);
CREATE INDEX idx_policy_violations_severity ON policy_violations(severity);
CREATE INDEX idx_policy_violations_resolved ON policy_violations(resolved);

-- ====================
-- SYSTEM PERFORMANCE
-- ====================
-- System-wide latency, throughput, and health metrics
CREATE TABLE IF NOT EXISTS system_performance (
    id SERIAL PRIMARY KEY,
    measured_at TIMESTAMP NOT NULL,
    measurement_window INTEGER NOT NULL DEFAULT 60,  -- seconds

    -- Throughput
    requests_per_second FLOAT NOT NULL,
    total_requests INTEGER NOT NULL,

    -- Latency (milliseconds)
    p50_latency_ms FLOAT,
    p95_latency_ms FLOAT,
    p99_latency_ms FLOAT,
    max_latency_ms FLOAT,
    avg_latency_ms FLOAT,

    -- Errors
    error_count INTEGER NOT NULL DEFAULT 0,
    error_rate FLOAT,
    timeout_count INTEGER NOT NULL DEFAULT 0,

    -- Resource utilization
    cpu_usage_percent FLOAT,
    memory_usage_mb FLOAT,

    -- Dependencies
    kafka_latency_ms FLOAT,
    redis_latency_ms FLOAT,
    db_latency_ms FLOAT,
    ml_inference_latency_ms FLOAT,

    -- SLO compliance
    slo_met BOOLEAN DEFAULT TRUE,
    slo_target_ms FLOAT DEFAULT 100.0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_perf_time ON system_performance(measured_at DESC);
CREATE INDEX idx_system_perf_slo ON system_performance(slo_met);

-- ====================
-- FINANCIAL METRICS
-- ====================
-- Daily financial rollups and cost analysis
CREATE TABLE IF NOT EXISTS financial_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,

    -- Transaction value
    total_value_processed BIGINT NOT NULL DEFAULT 0,
    total_transactions INTEGER NOT NULL DEFAULT 0,
    avg_transaction_value BIGINT NOT NULL DEFAULT 0,

    -- By decision type
    allowed_value BIGINT NOT NULL DEFAULT 0,
    escalated_value BIGINT NOT NULL DEFAULT 0,
    contained_value BIGINT NOT NULL DEFAULT 0,

    -- Fraud prevention
    fraud_attempts_detected INTEGER NOT NULL DEFAULT 0,
    fraud_value_prevented BIGINT NOT NULL DEFAULT 0,
    false_positives INTEGER NOT NULL DEFAULT 0,
    false_positive_rate FLOAT,

    -- Cost analysis
    authorization_count INTEGER NOT NULL DEFAULT 0,
    cost_per_authorization NUMERIC(10, 4) DEFAULT 0.01,  -- USD
    total_operational_cost NUMERIC(12, 2),

    -- ROI metrics
    fraud_prevention_savings BIGINT NOT NULL DEFAULT 0,
    net_value NUMERIC(15, 2),  -- savings minus costs
    roi_percentage FLOAT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_financial_metrics_date ON financial_metrics(date DESC);

-- ====================
-- ANOMALY DETECTIONS
-- ====================
-- Detected anomalies in agent behavior, transaction patterns
CREATE TABLE IF NOT EXISTS anomaly_detections (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMP NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,  -- 'velocity', 'volume', 'pattern', 'behavioral'
    severity VARCHAR(20) NOT NULL,  -- 'low', 'medium', 'high', 'critical'

    -- Subject
    entity_type VARCHAR(50) NOT NULL,  -- 'agent', 'system', 'recipient'
    entity_id VARCHAR(255),

    -- Details
    description TEXT NOT NULL,
    baseline_value FLOAT,
    current_value FLOAT,
    deviation_score FLOAT,  -- Standard deviations from baseline

    -- Context
    affected_intents INTEGER DEFAULT 0,
    affected_agents INTEGER DEFAULT 0,

    -- Response
    alerted BOOLEAN DEFAULT FALSE,
    alerted_at TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP,
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_anomaly_detected ON anomaly_detections(detected_at DESC);
CREATE INDEX idx_anomaly_type ON anomaly_detections(anomaly_type);
CREATE INDEX idx_anomaly_severity ON anomaly_detections(severity);
CREATE INDEX idx_anomaly_ack ON anomaly_detections(acknowledged);

-- ====================
-- PREDICTIONS
-- ====================
-- Forecasted metrics for capacity planning
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    prediction_date DATE NOT NULL,
    predicted_for_date DATE NOT NULL,
    prediction_type VARCHAR(50) NOT NULL,  -- 'volume', 'fraud_rate', 'load'

    -- Prediction
    predicted_value FLOAT NOT NULL,
    confidence_lower FLOAT,
    confidence_upper FLOAT,
    confidence_level FLOAT DEFAULT 0.95,

    -- Model info
    model_version VARCHAR(50),
    model_accuracy FLOAT,

    -- Actual (filled in later)
    actual_value FLOAT,
    prediction_error FLOAT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(prediction_date, predicted_for_date, prediction_type)
);

CREATE INDEX idx_predictions_for_date ON predictions(predicted_for_date);
CREATE INDEX idx_predictions_type ON predictions(prediction_type);

-- ====================
-- REPORTS
-- ====================
-- Generated reports metadata and storage
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    report_id VARCHAR(255) UNIQUE NOT NULL,
    report_type VARCHAR(50) NOT NULL,  -- 'daily', 'weekly', 'monthly', 'custom'
    report_format VARCHAR(20) NOT NULL,  -- 'pdf', 'csv', 'json', 'excel'

    -- Time range
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    -- Content
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    data_snapshot JSONB,  -- Key metrics snapshot

    -- Storage
    file_path VARCHAR(500),
    file_size_bytes BIGINT,

    -- Access
    generated_by VARCHAR(255),
    shared_with TEXT[],  -- Array of user IDs/emails
    access_level VARCHAR(20) DEFAULT 'private',  -- 'private', 'team', 'public'

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_reports_type ON reports(report_type);
CREATE INDEX idx_reports_created ON reports(created_at DESC);
CREATE INDEX idx_reports_dates ON reports(start_date, end_date);

-- ====================
-- DATA RETENTION POLICY
-- ====================
-- Automatically partition and archive old data
-- Raw audit logs: 90 days
-- Aggregated metrics: 1 year
-- Reports: 2 years

COMMENT ON TABLE decisions_aggregated IS 'Hourly/daily rollups of authorization decisions - 1 year retention';
COMMENT ON TABLE agent_metrics IS 'Per-agent performance metrics - 1 year retention';
COMMENT ON TABLE fraud_events IS 'Detected fraud attempts - 2 year retention for compliance';
COMMENT ON TABLE policy_violations IS 'Policy breach records - 2 year retention for compliance';
COMMENT ON TABLE system_performance IS 'System health metrics - 90 days retention';
COMMENT ON TABLE financial_metrics IS 'Daily financial rollups - permanent retention';
COMMENT ON TABLE anomaly_detections IS 'Anomaly detection log - 1 year retention';
COMMENT ON TABLE predictions IS 'Forecasts and actuals - 1 year retention';
COMMENT ON TABLE reports IS 'Generated reports metadata - 2 year retention';
