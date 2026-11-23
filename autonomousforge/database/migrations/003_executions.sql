-- Execution System Tables
-- Migration: 003_executions.sql

-- Executions table
CREATE TABLE IF NOT EXISTS executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    command TEXT NOT NULL,
    working_directory TEXT,
    environment JSONB DEFAULT '{}',
    timeout_seconds INT DEFAULT 300,
    docker_image TEXT,
    docker_config JSONB DEFAULT '{}',
    status VARCHAR(30) NOT NULL DEFAULT 'queued',  -- queued, running, completed, failed, cancelled, timeout
    exit_code INT,
    stdout TEXT,
    stderr TEXT,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_executions_project ON executions(project_id);
CREATE INDEX IF NOT EXISTS idx_executions_task ON executions(task_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_queued ON executions(queued_at) WHERE status IN ('queued', 'running');

-- Sandboxes table
CREATE TABLE IF NOT EXISTS sandboxes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    base_image VARCHAR(200) DEFAULT 'python:3.11-slim',
    environment JSONB DEFAULT '{}',
    ports JSONB DEFAULT '[]',
    volumes JSONB DEFAULT '[]',
    resources JSONB DEFAULT '{}',
    auto_destroy_seconds INT DEFAULT 3600,
    status VARCHAR(30) NOT NULL DEFAULT 'creating',  -- creating, running, stopped, destroyed
    container_id VARCHAR(64),
    endpoint TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sandboxes_project ON sandboxes(project_id);
CREATE INDEX IF NOT EXISTS idx_sandboxes_status ON sandboxes(status);
CREATE INDEX IF NOT EXISTS idx_sandboxes_expires ON sandboxes(expires_at) WHERE status IN ('running', 'stopped');

-- Apply updated_at triggers
CREATE TRIGGER update_executions_updated_at BEFORE UPDATE ON executions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sandboxes_updated_at BEFORE UPDATE ON sandboxes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();