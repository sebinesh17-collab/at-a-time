-- AUTONOMOUSFORGE Database Schema
-- Single-owner autonomous multi-agent software engineering OS

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Owner table (single row only)
CREATE TABLE owner (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    password_hash TEXT NOT NULL,
    master_api_key_hash TEXT NOT NULL,
    two_fa_secret TEXT,
    is_setup_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES owner(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    refresh_token_hash TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    refresh_expires_at TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN GENERATED ALWAYS AS (revoked_at IS NULL AND expires_at > NOW()) STORED
);

CREATE INDEX idx_sessions_owner_id ON sessions(owner_id);
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- API Keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    key_label VARCHAR(100) NOT NULL,
    key_hash TEXT NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,  -- First 8 chars for identification
    is_enabled BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count BIGINT DEFAULT 0,
    quota_limit BIGINT,
    quota_used BIGINT DEFAULT 0,
    quota_reset_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    health_status VARCHAR(20) DEFAULT 'unknown',  -- unknown, healthy, degraded, failed
    failure_count INT DEFAULT 0,
    consecutive_failures INT DEFAULT 0,
    last_health_check TIMESTAMP WITH TIME ZONE,
    concurrency_limit INT DEFAULT 10,
    weight INT DEFAULT 100,  -- For weighted allocation
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_api_keys_provider ON api_keys(provider);
CREATE INDEX idx_api_keys_enabled ON api_keys(is_enabled) WHERE is_enabled = TRUE;
CREATE INDEX idx_api_keys_health ON api_keys(health_status);

-- Agents Registry (16,111 logical agents)
CREATE TABLE agents (
    id VARCHAR(20) PRIMARY KEY,  -- M-001, P-01, H-001, TL-001, W-0001
    name VARCHAR(200) NOT NULL,
    role VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    level INT NOT NULL CHECK (level BETWEEN 0 AND 4),  -- 0=Master, 1=Principal, 2=Head, 3=TeamLeader, 4=Worker
    parent_id VARCHAR(20) REFERENCES agents(id),
    system_prompt TEXT,
    model_id VARCHAR(100),
    provider VARCHAR(50) DEFAULT 'nvidia',
    tools JSONB DEFAULT '[]',
    skills JSONB DEFAULT '[]',
    permissions JSONB DEFAULT '{}',
    memory_config JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'idle',  -- idle, active, paused, error
    current_task_id UUID,
    tasks_completed BIGINT DEFAULT 0,
    tasks_failed BIGINT DEFAULT 0,
    avg_execution_time_ms BIGINT DEFAULT 0,
    last_active_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agents_level ON agents(level);
CREATE INDEX idx_agents_department ON agents(department);
CREATE INDEX idx_agents_parent ON agents(parent_id);
CREATE INDEX idx_agents_status ON agents(status);

-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    project_type VARCHAR(50),  -- mobile-android, mobile-ios, mobile-cross, web, backend, api, database, ai, automation, fullstack
    tech_stack JSONB DEFAULT '[]',
    status VARCHAR(30) DEFAULT 'planning',  -- planning, active, building, testing, deployed, archived
    owner_id UUID NOT NULL REFERENCES owner(id),
    repository_url TEXT,
    branch_name VARCHAR(100) DEFAULT 'main',
    deployment_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_type ON projects(project_type);

-- Tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    assigned_agent_id VARCHAR(20) REFERENCES agents(id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(50),  -- epic, feature, task, subtask, microtask, atomic
    priority INT DEFAULT 0,  -- Higher = more urgent
    dependencies UUID[] DEFAULT '{}',
    required_skills JSONB DEFAULT '[]',
    required_tools JSONB DEFAULT '[]',
    selected_model VARCHAR(100),
    selected_provider VARCHAR(50),
    expected_output JSONB,
    acceptance_criteria JSONB,
    status VARCHAR(30) DEFAULT 'pending',  -- pending, queued, running, completed, failed, cancelled, blocked
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    error_message TEXT,
    result JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_agent ON tasks(assigned_agent_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_parent ON tasks(parent_task_id);
CREATE INDEX idx_tasks_priority ON tasks(priority DESC);
CREATE INDEX idx_tasks_queued ON tasks(queued_at) WHERE status IN ('pending', 'queued');

-- Messages (Agent Communication)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    sender_id VARCHAR(20) REFERENCES agents(id) ON DELETE SET NULL,
    recipient_id VARCHAR(20) REFERENCES agents(id) ON DELETE SET NULL,
    message_type VARCHAR(50) NOT NULL,  -- task_assignment, task_acceptance, progress_update, completion, error_report, review_request, integration_request, approval_request, escalation
    content JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'sent',  -- sent, delivered, read, processed
    output_references JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_messages_task ON messages(task_id);
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_recipient ON messages(recipient_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);

-- Files table
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    owner_id UUID NOT NULL REFERENCES owner(id),
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL,
    storage_path TEXT NOT NULL,
    storage_provider VARCHAR(50) DEFAULT 'local',  -- local, s3, r2
    checksum_sha256 VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    extracted_content TEXT,
    analysis_result JSONB,
    is_processed BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(30) DEFAULT 'pending',
    processing_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_files_project ON files(project_id);
CREATE INDEX idx_files_owner ON files(owner_id);
CREATE INDEX idx_files_mime ON files(mime_type);
CREATE INDEX idx_files_processed ON files(is_processed);

-- Conversations (Chat History)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    owner_id UUID NOT NULL REFERENCES owner(id),
    title VARCHAR(500),
    mode VARCHAR(20) DEFAULT 'chat',  -- chat, chat_files, chat_files_skills
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conversations_owner ON conversations(owner_id);
CREATE INDEX idx_conversations_project ON conversations(project_id);

-- Chat Messages
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- user, assistant, system, tool
    content TEXT NOT NULL,
    attachments JSONB DEFAULT '[]',
    tool_calls JSONB DEFAULT '[]',
    tool_results JSONB DEFAULT '[]',
    model_used VARCHAR(100),
    tokens_input INT,
    tokens_output INT,
    latency_ms INT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_conversation ON chat_messages(conversation_id);
CREATE INDEX idx_chat_messages_created ON chat_messages(created_at);

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_type VARCHAR(20) NOT NULL,  -- owner, agent, system
    actor_id VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_actor ON audit_logs(actor_type, actor_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);

-- Knowledge / Vector Embeddings
CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- Adjust dimension based on model
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_knowledge_project ON knowledge_chunks(project_id);
CREATE INDEX idx_knowledge_file ON knowledge_chunks(file_id);
CREATE INDEX idx_knowledge_embedding ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Workflows
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    definition JSONB NOT NULL,  -- React Flow compatible
    version INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(20) REFERENCES agents(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow Executions
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    trigger_type VARCHAR(50),  -- manual, scheduled, event, webhook
    trigger_data JSONB DEFAULT '{}',
    status VARCHAR(30) DEFAULT 'running',  -- running, completed, failed, cancelled
    current_node_id VARCHAR(100),
    execution_data JSONB DEFAULT '{}',
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_workflow_exec_workflow ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_exec_status ON workflow_executions(status);

-- Skills
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,  -- coding, architecture, research, debugging, testing, security, database, mobile, frontend, backend, devops, documentation
    description TEXT,
    prompt_template TEXT,
    parameters JSONB DEFAULT '{}',
    required_tools JSONB DEFAULT '[]',
    is_system BOOLEAN DEFAULT FALSE,
    is_enabled BOOLEAN DEFAULT TRUE,
    version INT DEFAULT 1,
    created_by VARCHAR(20) REFERENCES agents(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_skills_enabled ON skills(is_enabled) WHERE is_enabled = TRUE;

-- Tools
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,  -- browser, search, terminal, filesystem, git, github, http, api, database, build, testing, cloud
    description TEXT,
    schema JSONB NOT NULL,  -- JSON Schema for tool parameters
    implementation_type VARCHAR(50),  -- builtin, mcp, custom
    implementation_config JSONB DEFAULT '{}',
    required_permissions JSONB DEFAULT '[]',
    is_system BOOLEAN DEFAULT FALSE,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tools_category ON tools(category);
CREATE INDEX idx_tools_enabled ON tools(is_enabled) WHERE is_enabled = TRUE;

-- MCP Servers
CREATE TABLE mcp_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    transport VARCHAR(20) NOT NULL,  -- stdio, sse, websocket
    connection_config JSONB NOT NULL,
    auth_config JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'disconnected',  -- connected, disconnected, error
    last_connected TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Memory
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_type VARCHAR(30) NOT NULL,  -- owner, conversation, project, agent, workflow, execution, technical_decision
    owner_id UUID REFERENCES owner(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    agent_id VARCHAR(20) REFERENCES agents(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    key VARCHAR(500) NOT NULL,
    value JSONB NOT NULL,
    embedding VECTOR(1536),
    importance FLOAT DEFAULT 1.0,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_memories_type_owner ON memories(memory_type, owner_id);
CREATE INDEX idx_memories_project ON memories(project_id);
CREATE INDEX idx_memories_agent ON memories(agent_id);
CREATE INDEX idx_memories_key ON memories(key);
CREATE INDEX idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_owner_updated_at BEFORE UPDATE ON owner FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_files_updated_at BEFORE UPDATE ON files FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_skills_updated_at BEFORE UPDATE ON skills FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tools_updated_at BEFORE UPDATE ON tools FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mcp_servers_updated_at BEFORE UPDATE ON mcp_servers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON memories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to enforce single owner
CREATE OR REPLACE FUNCTION enforce_single_owner()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT COUNT(*) FROM owner) >= 1 AND TG_OP = 'INSERT' THEN
        RAISE EXCEPTION 'Only one owner account is allowed. Registration is disabled.';
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER enforce_single_owner_trigger
BEFORE INSERT ON owner
FOR EACH ROW EXECUTE FUNCTION enforce_single_owner();