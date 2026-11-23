# AUTONOMOUSFORGE Implementation Plan

## Project Overview
Private Autonomous Multi-Agent Software Engineering OS for single owner (BOSS/Sebinesh)

## Technology Stack

### Frontend
- **HTML/JavaScript/CSS** (Vanilla, no framework per requirements)
- Tailwind CSS via CDN
- Vanilla JS modules for state management

### Backend
- **Python** (no FastAPI - using standard library + aiohttp/starlette)
- aiohttp for async HTTP server
- asyncpg for PostgreSQL
- redis-py for Redis
- argon2-cffi for password hashing
- python-jose for JWT

### Database
- PostgreSQL (primary)
- Redis (caching, queues, sessions)

### AI Provider
- NVIDIA NIM API (primary)
- OpenAI-compatible interface

### Infrastructure
- Docker Compose for local development
- Linux containers for worker isolation

---

## Phase 1: Foundation & Authentication (Week 1-2)

### 1.1 Project Structure & Config
- [ ] Docker Compose with PostgreSQL, Redis
- [ ] Environment configuration (.env.example)
- [ ] Python backend entry point
- [ ] Frontend HTML/CSS/JS structure

### 1.2 Database Schema
- [ ] Owner table (single row)
- [ ] Sessions table
- [ ] API Keys table
- [ ] Agents registry table
- [ ] Tasks table
- [ ] Messages table
- [ ] Projects table
- [ ] Audit logs table

### 1.3 Authentication System
- [ ] Owner registration (first-time setup)
- [ ] Argon2id password hashing
- [ ] JWT session management
- [ ] Master API key generation
- [ ] Rate limiting & brute force protection
- [ ] Secure cookies (HttpOnly, Secure, SameSite)

### 1.4 Frontend - Login & Dashboard
- [ ] Login page with secure form
- [ ] Dashboard layout with navigation
- [ ] Chat interface (Mode 1: Normal Chat)
- [ ] WebSocket/SSE for streaming responses

---

## Phase 2: NVIDIA Integration & Model Router (Week 2-3)

### 2.1 NVIDIA Provider Service
- [ ] NVIDIA API client
- [ ] Model discovery from catalog
- [ ] Health checks for API keys
- [ ] Usage/quota monitoring

### 2.2 API Key Vault
- [ ] Encrypted storage for multiple keys
- [ ] Key rotation & health checks
- [ ] Selection strategies (round-robin, weighted, least-utilized)
- [ ] Quota-aware routing

### 2.3 Model Router
- [ ] Task classification (coding, reasoning, research, vision, etc.)
- [ ] Model capability matching
- [ ] Cost/latency optimization
- [ ] Fallback chains

---

## Phase 3: 16,111 Agent Registry (Week 3-4)

### 3.1 Agent Data Model
- [ ] Agent hierarchy (Master → Principals → Heads → Team Leaders → Workers)
- [ ] Agent configuration (prompts, models, tools, skills, permissions)
- [ ] Persistent registry in PostgreSQL

### 3.2 Agent Generation
- [ ] Programmatic generation of 16,111 logical agents
- [ ] Stable IDs: `M-001`, `P-01` to `P-10`, `H-001` to `H-100`, `TL-001` to `TL-1000`, `W-0001` to `W-15000`
- [ ] Department assignment

### 3.3 Command Center UI
- [ ] Hierarchical visualization
- [ ] Search, filter, pagination
- [ ] Agent profile viewer
- [ ] Performance metrics

---

## Phase 4: Task Engine & Communication (Week 4-5)

### 4.1 Task Decomposition
- [ ] Project → Epic → Feature → Task → Subtask → Microtask → Atomic
- [ ] DAG-based execution
- [ ] Dependency resolution
- [ ] Parallel/sequential execution

### 4.2 Message Bus
- [ ] Structured message format
- [ ] Durable queue (Redis Streams / BullMQ equivalent)
- [ ] Hierarchical routing
- [ ] Cross-department communication

### 4.3 Worker Runtime
- [ ] Task leasing & heartbeats
- [ ] Retry with backoff
- [ ] Work stealing
- [ ] Resource bounds (CPU, RAM, time)

---

## Phase 5: File Upload & Knowledge (Week 5-6)

### 5.1 File Processing
- [ ] Multi-format support (PDF, DOCX, code, archives, images)
- [ ] MIME detection, size limits
- [ ] Secure storage (S3/R2 compatible)
- [ ] OCR, code parsing, archive inspection

### 5.2 Knowledge Management
- [ ] Document chunking
- [ ] Embeddings (NVIDIA or local)
- [ ] Vector search (pgvector/Qdrant)
- [ ] RAG integration

---

## Phase 6: Cloud Linux & Development Tools (Week 6-7)

### 6.1 Execution Environment
- [ ] Container sandboxing
- [ ] Language runtimes (Python, Node, Java, Kotlin, Flutter, Android SDK)
- [ ] Terminal access
- [ ] File manager

### 6.2 Git Integration
- [ ] Repository management
- [ ] Branch/worktree per agent
- [ ] Commit, PR automation

---

## Phase 7: Mobile & Web Development Engines (Week 7-9)

### 7.1 Mobile Generation
- [ ] Android (Kotlin, Jetpack Compose, Gradle)
- [ ] iOS (Swift, SwiftUI, project generation)
- [ ] Cross-platform (Flutter, React Native)

### 7.2 Web Generation
- [ ] React, Vue, Svelte projects
- [ ] Backend APIs (Python, Node)
- [ ] Database schema generation
- [ ] Build & preview

---

## Phase 8: Skills, Tools, MCP & Workflows (Week 9-10)

### 8.1 Skills System
- [ ] Visual skill builder
- [ ] Categories: coding, architecture, research, debugging, testing, security, database, mobile, frontend, backend, DevOps, documentation

### 8.2 Tools & MCP
- [ ] Tool registry (browser, search, terminal, filesystem, git, HTTP, database, build, test, cloud)
- [ ] MCP client integration
- [ ] Permission system

### 8.3 Workflow Builder
- [ ] React Flow based editor
- [ ] Node types: agents, LLM, tools, conditions, parallel/sequential, human approval
- [ ] Execution & debugging

---

## Phase 9: Security, Monitoring, Testing (Week 10-11)

### 9.1 Security
- [ ] RBAC for agents
- [ ] Sandbox isolation
- [ ] Audit logging
- [ ] Backup encryption

### 9.2 Monitoring
- [ ] Real-time metrics (WebSocket/SSE)
- [ ] Agent activity, queue depth, model usage
- [ ] Resource utilization
- [ ] Alerting

### 9.3 Testing
- [ ] Unit/integration tests
- [ ] E2E test automation
- [ ] Load testing

---

## Phase 10: Integration & Deployment (Week 11-12)

### 10.1 Full Integration
- [ ] End-to-end workflows
- [ ] Owner control center
- [ ] Emergency stops
- [ ] Resource budgets

### 10.2 Deployment
- [ ] Docker images
- [ ] Kubernetes/compose configs
- [ ] CI/CD pipelines
- [ ] Health checks, rollback

---

## Database Schema (PostgreSQL)

```sql
-- Owner (single row)
CREATE TABLE owner (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    password_hash TEXT NOT NULL,
    master_api_key_hash TEXT NOT NULL,
    two_fa_secret TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES owner(id),
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP
);

-- API Keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    key_label VARCHAR(100) NOT NULL,
    key_hash TEXT NOT NULL,
    is_enabled BOOLEAN DEFAULT true,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    usage_count BIGINT DEFAULT 0,
    quota_limit BIGINT,
    quota_used BIGINT DEFAULT 0,
    health_status VARCHAR(20) DEFAULT 'unknown',
    failure_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agents Registry (16,111 logical agents)
CREATE TABLE agents (
    id VARCHAR(20) PRIMARY KEY,  -- M-001, P-01, H-001, TL-001, W-0001
    name VARCHAR(200) NOT NULL,
    role VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    level INT NOT NULL,  -- 0=Master, 1=Principal, 2=Head, 3=TeamLeader, 4=Worker
    parent_id VARCHAR(20) REFERENCES agents(id),
    system_prompt TEXT,
    model_id VARCHAR(100),
    provider VARCHAR(50),
    tools JSONB DEFAULT '[]',
    skills JSONB DEFAULT '[]',
    permissions JSONB DEFAULT '{}',
    memory_config JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'idle',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    parent_task_id UUID REFERENCES tasks(id),
    assigned_agent_id VARCHAR(20) REFERENCES agents(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(50),
    priority INT DEFAULT 0,
    dependencies UUID[],
    required_skills JSONB DEFAULT '[]',
    required_tools JSONB DEFAULT '[]',
    selected_model VARCHAR(100),
    expected_output JSONB,
    acceptance_criteria JSONB,
    status VARCHAR(30) DEFAULT 'pending',
    retry_count INT DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Messages (Agent Communication)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    task_id UUID REFERENCES tasks(id),
    sender_id VARCHAR(20) REFERENCES agents(id),
    recipient_id VARCHAR(20) REFERENCES agents(id),
    message_type VARCHAR(50),
    content JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'sent',
    output_references JSONB DEFAULT '[]'
);

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    project_type VARCHAR(50),
    tech_stack JSONB,
    status VARCHAR(30) DEFAULT 'planning',
    owner_id UUID REFERENCES owner(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_type VARCHAR(20),  -- 'owner', 'agent', 'system'
    actor_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

### Auth
- `POST /api/auth/setup` - First-time owner setup
- `POST /api/auth/login` - Owner login
- `POST /api/auth/logout` - Logout
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/change-password` - Change password
- `GET /api/auth/me` - Current owner info

### Master API Key
- `POST /api/auth/master-key` - Generate master key (owner only)
- `GET /api/auth/master-key` - View master key info
- `DELETE /api/auth/master-key` - Revoke master key

### Agents
- `GET /api/agents` - List agents (paginated, filterable)
- `GET /api/agents/:id` - Get agent details
- `GET /api/agents/hierarchy` - Full hierarchy tree
- `POST /api/agents/:id/pause` - Pause agent
- `POST /api/agents/:id/resume` - Resume agent

### Tasks
- `POST /api/tasks` - Create task
- `GET /api/tasks` - List tasks
- `GET /api/tasks/:id` - Get task details
- `GET /api/tasks/:id/subtasks` - Get subtasks
- `POST /api/tasks/:id/execute` - Execute task

### Chat
- `POST /api/chat` - Send message (streaming response)
- `GET /api/chat/history` - Conversation history
- `POST /api/chat/new` - New conversation

### Model Gateway
- `POST /api/models/complete` - Model completion
- `GET /api/models` - Available models
- `GET /api/models/:id` - Model details

### API Keys
- `POST /api/keys` - Add API key
- `GET /api/keys` - List keys
- `PUT /api/keys/:id` - Update key
- `DELETE /api/keys/:id` - Revoke key
- `POST /api/keys/:id/health` - Check health

### Projects
- `POST /api/projects` - Create project
- `GET /api/projects` - List projects
- `GET /api/projects/:id` - Project details
- `PUT /api/projects/:id` - Update project

### Files
- `POST /api/files/upload` - Upload file
- `GET /api/files/:id` - Download file
- `POST /api/files/:id/analyze` - Analyze file
- `DELETE /api/files/:id` - Delete file

---

## File Structure Details

### Backend (services/)
```
services/
├── api-gateway/          # Main entry point, routing, middleware
├── auth-service/         # Authentication, sessions, master key
├── master-orchestrator/  # Master agent logic, task planning
├── agent-registry/       # Agent CRUD, hierarchy management
├── task-scheduler/       # Task queue, DAG execution, dependencies
├── worker-runtime/       # Worker execution, sandboxing
├── model-gateway/        # Model routing, NVIDIA integration
├── provider-service/     # API key vault, health checks
├── vault-service/        # Secret encryption/decryption
├── file-service/         # File upload, processing, storage
├── memory-service/       # Persistent memory, conversation history
├── knowledge-service/    # RAG, embeddings, vector search
├── execution-service/    # Code execution, build, test
├── build-service/        # Project building (mobile, web)
├── testing-service/      # Test execution, reporting
└── monitoring-service/   # Metrics, health, alerts
```

### Frontend (apps/web/)
```
apps/web/
├── index.html            # Main entry (login or dashboard)
├── login.html            # Login page
├── dashboard.html        # Main dashboard
├── chat.html             # Chat interface
├── agents.html           # Agent command center
├── projects.html         # Project management
├── settings.html         # Settings, API keys
├── css/
│   ├── main.css          # Main styles
│   ├── components.css    # Component styles
│   └── dashboard.css     # Dashboard specific
├── js/
│   ├── main.js           # App initialization
│   ├── auth.js           # Authentication
│   ├── chat.js           # Chat interface
│   ├── agents.js         # Agent command center
│   ├── projects.js       # Project management
│   ├── settings.js       # Settings
│   ├── api.js            # API client
│   ├── websocket.js      # WebSocket/SSE client
│   └── utils.js          # Utilities
└── assets/               # Images, icons
```

---

## Implementation Order

1. **Week 1**: Docker setup, database, Python backend skeleton, auth service
2. **Week 2**: Frontend login/dashboard, chat interface, WebSocket
3. **Week 3**: NVIDIA integration, model router, API key vault
4. **Week 4**: Agent registry generation (16,111), command center UI
5. **Week 5**: Task engine, message bus, worker runtime
6. **Week 6**: File upload, knowledge management
7. **Week 7**: Cloud Linux environment, Git integration
8. **Week 8-9**: Mobile/web development engines
8. **Week 10**: Skills, tools, MCP, workflow builder
9. **Week 11**: Security hardening, monitoring, testing
10. **Week 12**: Full integration, deployment, documentation

---

## Key Implementation Decisions

1. **No FastAPI**: Using aiohttp + custom routing for full control
2. **Single Owner**: Hardcoded single-owner architecture, no multi-tenancy
3. **Master API Key**: One key controls everything - owner can talk to any agent, read any database
4. **16,111 Logical Agents**: Generated programmatically, not 16k running processes
5. **NVIDIA Primary**: All model routing defaults to NVIDIA NIM
6. **Mobile First**: Android/iOS generation as primary targets
7. **Real Execution**: No fake responses, real API calls, real task execution