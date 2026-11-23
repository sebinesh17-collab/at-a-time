-- Build System Tables
-- Migration: 002_builds.sql

-- Builds table
CREATE TABLE IF NOT EXISTS builds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    trigger_type VARCHAR(50) NOT NULL DEFAULT 'manual',  -- manual, push, pr, scheduled, webhook
    trigger_data JSONB DEFAULT '{}',
    branch_name VARCHAR(100) DEFAULT 'main',
    commit_sha VARCHAR(64),
    build_config JSONB DEFAULT '{}',
    status VARCHAR(30) NOT NULL DEFAULT 'queued',  -- queued, running, completed, failed, cancelled
    current_stage VARCHAR(100),
    progress INT DEFAULT 0,
    logs TEXT,
    artifacts JSONB DEFAULT '[]',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_builds_project ON builds(project_id);
CREATE INDEX IF NOT EXISTS idx_builds_status ON builds(status);
CREATE INDEX IF NOT EXISTS idx_builds_queued ON builds(queued_at) WHERE status IN ('queued', 'running');

-- Build Stages table
CREATE TABLE IF NOT EXISTS build_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    build_id UUID NOT NULL REFERENCES builds(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    "order" INT NOT NULL,
    commands JSONB DEFAULT '[]',
    environment JSONB DEFAULT '{}',
    timeout_seconds INT DEFAULT 300,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed, skipped
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    logs TEXT,
    exit_code INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_build_stages_build ON build_stages(build_id);
CREATE INDEX IF NOT EXISTS idx_build_stages_order ON build_stages(build_id, "order");

-- Build Logs table
CREATE TABLE IF NOT EXISTS build_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    build_id UUID NOT NULL REFERENCES builds(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES build_stages(id) ON DELETE CASCADE,
    level VARCHAR(20) NOT NULL DEFAULT 'info',  -- debug, info, warn, error
    message TEXT NOT NULL,
    source VARCHAR(50) DEFAULT 'build',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_build_logs_build ON build_logs(build_id);
CREATE INDEX IF NOT EXISTS idx_build_logs_stage ON build_logs(stage_id);
CREATE INDEX IF NOT EXISTS idx_build_logs_timestamp ON build_logs(timestamp);

-- Apply updated_at triggers
CREATE TRIGGER update_builds_updated_at BEFORE UPDATE ON builds FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_build_stages_updated_at BEFORE UPDATE ON build_stages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();