-- Testing System Tables
-- Migration: 005_testing.sql

-- Test Suites table
CREATE TABLE IF NOT EXISTS test_suites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    test_type VARCHAR(50) NOT NULL,  -- unit, integration, e2e, performance, security, load
    configuration JSONB DEFAULT '{}',
    environment JSONB DEFAULT '{}',
    schedule VARCHAR(100),  -- cron expression
    is_enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    last_status VARCHAR(30),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_test_suites_project ON test_suites(project_id);
CREATE INDEX IF NOT EXISTS idx_test_suites_type ON test_suites(test_type);
CREATE INDEX IF NOT EXISTS idx_test_suites_enabled ON test_suites(is_enabled) WHERE is_enabled = TRUE;

-- Test Cases table
CREATE TABLE IF NOT EXISTS test_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    suite_id UUID NOT NULL REFERENCES test_suites(id) ON DELETE CASCADE,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    test_code TEXT NOT NULL,
    dependencies JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',
    timeout_seconds INT DEFAULT 60,
    retries INT DEFAULT 0,
    is_flaky BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_test_cases_suite ON test_cases(suite_id);
CREATE INDEX IF NOT EXISTS idx_test_cases_tags ON test_cases(tags);

-- Test Runs table
CREATE TABLE IF NOT EXISTS test_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    suite_id UUID NOT NULL REFERENCES test_suites(id) ON DELETE CASCADE,
    trigger_type VARCHAR(50) NOT NULL DEFAULT 'manual',  -- manual, scheduled, push, pr, api
    trigger_data JSONB DEFAULT '{}',
    environment JSONB DEFAULT '{}',
    status VARCHAR(30) NOT NULL DEFAULT 'queued',  -- queued, running, completed, failed, cancelled
    current_case VARCHAR(500),
    progress INT DEFAULT 0,
    total_cases INT DEFAULT 0,
    passed INT DEFAULT 0,
    failed INT DEFAULT 0,
    skipped INT DEFAULT 0,
    errored INT DEFAULT 0,
    duration_ms INT DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_test_runs_suite ON test_runs(suite_id);
CREATE INDEX IF NOT EXISTS idx_test_runs_status ON test_runs(status);
CREATE INDEX IF NOT EXISTS idx_test_runs_queued ON test_runs(queued_at) WHERE status IN ('queued', 'running');

-- Test Results table
CREATE TABLE IF NOT EXISTS test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES test_runs(id) ON DELETE CASCADE,
    case_id UUID NOT NULL REFERENCES test_cases(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,  -- passed, failed, skipped, errored
    duration_ms INT NOT NULL,
    output TEXT,
    error_message TEXT,
    stack_trace TEXT,
    assertions JSONB DEFAULT '[]',
    coverage JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_test_results_run ON test_results(run_id);
CREATE INDEX IF NOT EXISTS idx_test_results_case ON test_results(case_id);
CREATE INDEX IF NOT EXISTS idx_test_results_status ON test_results(status);

-- Apply updated_at triggers
CREATE TRIGGER update_test_suites_updated_at BEFORE UPDATE ON test_suites FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_test_cases_updated_at BEFORE UPDATE ON test_cases FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_test_runs_updated_at BEFORE UPDATE ON test_runs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();