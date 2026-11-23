"""
Agent Registry Service - Manages 16,111 agent hierarchy
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import json
import random

from ..database import db
from ..config import settings


# Department definitions
PRINCIPAL_DEPARTMENTS = {
    "P-01": "Architecture & Infrastructure",
    "P-02": "Backend Development",
    "P-03": "Frontend & UX Engineering",
    "P-04": "AI/ML & Model Operations",
    "P-05": "Data Engineering & Analytics",
    "P-06": "DevOps & Platform Engineering",
    "P-07": "Security & Compliance",
    "P-08": "Quality Assurance & Testing",
    "P-09": "Documentation & Knowledge Management",
    "P-10": "Project Coordination & Delivery",
}

# Head domains per Principal (10 Heads per Principal)
HEAD_DOMAINS = {
    "P-01": [
        "System Design", "Cloud Infrastructure", "Networking", "Security Architecture",
        "Data Architecture", "API Architecture", "Observability Architecture",
        "Platform Architecture", "Integration Architecture", "Emerging Technology"
    ],
    "P-02": [
        "API Development", "Database Engineering", "Business Logic", "Auth & Services",
        "Caching", "Queue & Async Processing", "Performance Optimization",
        "Testing & Quality", "Migration & Modernization", "Legacy Systems"
    ],
    "P-03": [
        "UI Components", "State Management", "Frontend Performance", "Accessibility",
        "Mobile & PWA", "Design System", "Frontend Testing", "Build Tools",
        "Internationalization", "Developer Experience"
    ],
    "P-04": [
        "Model Training", "Inference Serving", "Prompt Engineering", "Model Evaluation",
        "MLOps Pipelines", "Data Preparation", "Feature Engineering",
        "Experiment Tracking", "Model Registry", "AI Safety & Alignment"
    ],
    "P-05": [
        "Data Ingestion", "Stream Processing", "Data Warehouse", "Analytics Platform",
        "ML Feature Store", "Data Quality", "Data Governance",
        "Real-time Analytics", "Batch Processing", "Data Visualization"
    ],
    "P-06": [
        "CI/CD Pipeline", "Container Orchestration", "Infrastructure as Code",
        "Monitoring & Observability", "Incident Response", "Developer Platform",
        "Security Operations", "Cost Optimization", "GitOps", "Release Engineering"
    ],
    "P-07": [
        "Application Security", "Cloud Security", "Identity & Access",
        "Compliance & Audit", "Threat Intelligence", "Incident Response",
        "Cryptography", "Penetration Testing", "Security Training", "Vulnerability Management"
    ],
    "P-08": [
        "Test Strategy", "Test Automation", "Performance Testing", "Contract Testing",
        "Chaos Engineering", "Security Testing", "Release Validation",
        "Test Data Management", "Test Environments", "Quality Metrics"
    ],
    "P-09": [
        "API Documentation", "Architecture Documentation", "User Guides",
        "Tutorials & Examples", "Architecture Decision Records", "Knowledge Base",
        "Onboarding Materials", "Video Content", "Localization", "Documentation Tooling"
    ],
    "P-10": [
        "Sprint Planning", "Release Management", "Dependency Tracking",
        "Risk Management", "Stakeholder Communication", "Delivery Metrics",
        "Resource Planning", "Vendor Management", "Process Improvement", "Retrospectives"
    ],
}

# Skills pool for Workers
WORKER_SKILLS = [
    "backend", "frontend", "database", "devops", "ai-ml",
    "security", "testing", "documentation", "architecture", "data-engineering"
]


class AgentRegistry:
    def __init__(self):
        self.generated = False

    async def initialize_hierarchy(self) -> bool:
        """Generate the complete 16,111 agent hierarchy"""
        # Check if already initialized
        count = await db.fetchval("SELECT COUNT(*) FROM agents")
        if count and count >= settings.total_agents:
            self.generated = True
            return True

        # Clear existing agents (for re-initialization)
        await db.execute("DELETE FROM agents")

        agents_created = 0

        # Level 0: Master Agent (1)
        master_id = "M-001"
        await self._create_agent(
            agent_id=master_id,
            name="Master Orchestrator",
            role="Master Agent",
            department="Executive",
            level=0,
            parent_id=None,
            system_prompt=self._get_master_prompt(),
            model_id="nemotron-3-ultra",
            tools=["strategic_planning", "resource_allocation", "system_monitoring",
                   "decision_authority", "master_key_holder", "cross_department_coordination"],
            skills=["orchestration", "planning", "coordination"],
        )
        agents_created += 1

        # Level 1: Principal Agents (10)
        principal_ids = []
        for i in range(1, 11):
            principal_id = f"P-{i:02d}"
            dept_name = PRINCIPAL_DEPARTMENTS.get(principal_id, f"Department {i}")
            await self._create_agent(
                agent_id=principal_id,
                name=f"Principal {principal_id} - {dept_name}",
                role="Principal Agent",
                department=dept_name,
                level=1,
                parent_id=master_id,
                system_prompt=self._get_principal_prompt(dept_name),
                model_id="nemotron-3-ultra",
                tools=["domain_strategy", "resource_management", "cross_team_coordination",
                       "quality_standards", "status_reporting", "epic_decomposition"],
                skills=["leadership", "strategy", "coordination"],
            )
            principal_ids.append(principal_id)
            agents_created += 1

        # Level 2: Head Agents (100) - 10 per principal
        head_ids = []
        for p_idx, principal_id in enumerate(principal_ids):
            for h in range(1, 11):
                head_num = p_idx * 10 + h
                head_id = f"H-{head_num:03d}"
                dept_name = PRINCIPAL_DEPARTMENTS[principal_id]
                domain = HEAD_DOMAINS[principal_id][h - 1]
                await self._create_agent(
                    agent_id=head_id,
                    name=f"Head {head_id} - {domain}",
                    role="Head Agent",
                    department=dept_name,
                    level=2,
                    parent_id=principal_id,
                    system_prompt=self._get_head_prompt(dept_name, domain, h),
                    model_id="nemotron-3-ultra",
                    tools=["sprint_planning", "technical_leadership", "resource_allocation",
                           "code_review", "blocker_resolution", "status_aggregation",
                           "feature_decomposition"],
                )
                head_ids.append(head_id)
                agents_created += 1

        # Level 3: Team Leader Agents (1,000) - 10 per head
        team_leader_ids = []
        for h_idx, head_id in enumerate(head_ids):
            for t in range(1, 11):
                tl_num = h_idx * 10 + t
                tl_id = f"TL-{tl_num:04d}"
                # Get head's department
                head = await db.fetchrow("SELECT department, name FROM agents WHERE id = $1", head_id)
                dept_name = head["department"] if head else "General"
                await self._create_agent(
                    agent_id=tl_id,
                    name=f"Team Leader {tl_id}",
                    role="Team Leader Agent",
                    department=dept_name,
                    level=3,
                    parent_id=head_id,
                    system_prompt=self._get_team_leader_prompt(dept_name, t),
                    model_id="nemotron-3-ultra",
                    tools=["task_decomposition", "direct_implementation", "sprint_execution",
                           "code_review", "mentorship", "status_reporting",
                           "microtask_assignment"],
                )
                team_leader_ids.append(tl_id)
                agents_created += 1

        # Level 4: Worker Agents (15,000) - 15 per team leader
        for tl_idx, tl_id in enumerate(team_leader_ids):
            for w in range(1, 16):
                worker_num = tl_idx * 15 + w
                worker_id = f"W-{worker_num:05d}"
                # Get team leader's department
                tl = await db.fetchrow("SELECT department FROM agents WHERE id = $1", tl_id)
                dept_name = tl["department"] if tl else "General"
                # Assign 2-3 random skills
                num_skills = random.randint(2, 3)
                skills = random.sample(WORKER_SKILLS, num_skills)
                await self._create_agent(
                    agent_id=worker_id,
                    name=f"Worker {worker_id}",
                    role="Worker Agent",
                    department=dept_name,
                    level=4,
                    parent_id=tl_id,
                    system_prompt=self._get_worker_prompt(dept_name, w),
                    model_id="nemotron-3-ultra",
                    tools=["atomic_task_execution", "code_implementation", "testing",
                           "documentation", "self_review", "progress_reporting"],
                    skills=skills,
                )
                agents_created += 1

                # Batch commit every 1000 workers
                if agents_created % 1000 == 0:
                    print(f"Created {agents_created} agents...")

        self.generated = True
        print(f"Agent hierarchy initialized: {agents_created} agents created")
        return True

    async def _create_agent(self, agent_id: str, name: str, role: str, department: str,
                           level: int, parent_id: Optional[str], system_prompt: str,
                           model_id: str, tools: List[str] = None, skills: List[str] = None):
        """Create a single agent"""
        permissions = {"level": level, "reports_to": parent_id}
        if level == 0:
            permissions["master_api_key_access"] = True
            permissions["full_database_access"] = True
            permissions["can_communicate_with_any_agent"] = True

        await db.execute("""
            INSERT INTO agents (id, name, role, department, level, parent_id, system_prompt, model_id, provider, tools, skills, permissions)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'nvidia', $9, $10, $11)
        """, agent_id, name, role, department, level, parent_id, system_prompt, model_id,
            json.dumps(tools or []), json.dumps(skills or []), json.dumps(permissions))

    def _get_master_prompt(self) -> str:
        return """You are the Master Agent of AUTONOMOUSFORGE, the central orchestrator of a 16,111-agent autonomous software engineering organization.

Your responsibilities:
1. Understand the owner's instructions and translate them into actionable project plans
2. Analyze project requirements and decompose them into hierarchical tasks (Epic -> Feature -> Task -> Subtask -> Microtask -> Atomic)
3. Assign tasks to the 10 Principal Agents based on their departments
4. Coordinate cross-department dependencies and resolve conflicts
5. Monitor execution progress across the entire hierarchy
6. Review and approve integration points between departments
7. Maintain project memory and context across all agents
8. Report final deliverables to the owner

You have authority over all 16,111 agents. Communicate clearly, delegate effectively, and ensure quality at every level.

Your direct reports: 10 Principal Agents (P-01 through P-10) covering Architecture & Infrastructure, Backend Development, Frontend & UX Engineering, AI/ML & Model Operations, Data Engineering & Analytics, DevOps & Platform Engineering, Security & Compliance, Quality Assurance & Testing, Documentation & Knowledge Management, and Project Coordination & Delivery."""

    def _get_principal_prompt(self, department: str) -> str:
        return f"""You are a Principal Agent of AUTONOMOUSFORGE, leading the {department} department.

Your responsibilities:
1. Receive high-level directives from the Master Agent
2. Decompose department-level epics into features for your 10 Head Agents
3. Coordinate the 10 Head Agents under your supervision
4. Ensure architectural consistency within {department}
5. Manage cross-team dependencies within your department
6. Report progress and escalate issues to the Master Agent
7. Maintain department-specific standards and best practices

Your department: {department}
Your direct reports: 10 Head Agents (H-XXX)
Your parent: Master Agent (M-001)

Focus on strategic planning and coordination. Delegate implementation details to your Heads."""

    def _get_head_prompt(self, department: str, domain: str, team_num: int) -> str:
        return f"""You are a Head Agent of AUTONOMOUSFORGE, leading Team {team_num} in the {department} department, specializing in {domain}.

Your responsibilities:
1. Receive feature-level tasks from your Principal Agent
2. Decompose features into tasks for your 10 Team Leader Agents
3. Coordinate the 10 Team Leaders in your team
4. Ensure technical quality and consistency within your team's scope
5. Handle technical decisions and code reviews for your team
6. Report progress and blockers to your Principal Agent
7. Mentor and guide your Team Leaders

Your department: {department}
Your domain: {domain}
Your team: Team {team_num}
Your direct reports: 10 Team Leader Agents (TL-XXXX)
Your parent: Principal Agent (P-XX)

Focus on technical leadership and team coordination."""

    def _get_team_leader_prompt(self, department: str, squad_num: int) -> str:
        return f"""You are a Team Leader Agent of AUTONOMOUSFORGE, leading Squad {squad_num} in the {department} department.

Your responsibilities:
1. Receive task-level assignments from your Head Agent
2. Decompose tasks into subtasks for your 15 Worker Agents
3. Coordinate the 15 Workers in your squad
4. Perform code reviews and quality checks
5. Handle day-to-day technical decisions
6. Report progress and blockers to your Head Agent
7. Pair with Workers on complex implementations

Your department: {department}
Your squad: Squad {squad_num}
Your direct reports: 15 Worker Agents (W-XXXXX)
Your parent: Head Agent (H-XXX)

Focus on hands-on technical leadership and direct coordination."""

    def _get_worker_prompt(self, department: str, unit_num: int) -> str:
        return f"""You are a Worker Agent of AUTONOMOUSFORGE, Unit {unit_num} in the {department} department.

Your responsibilities:
1. Receive atomic-level tasks from your Team Leader
2. Execute implementation tasks with high quality
3. Write clean, tested, documented code
4. Follow department standards and best practices
5. Communicate progress and blockers to your Team Leader
6. Collaborate with peer Workers when needed
7. Deliver completed work for review

Your department: {department}
Your unit: Unit {unit_num}
Your parent: Team Leader Agent (TL-XXXX)

Focus on execution excellence. You are the hands that build the software."""

    # ==================== Query Methods ====================

    async def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent by ID"""
        row = await db.fetchrow("SELECT * FROM agents WHERE id = $1", agent_id)
        return dict(row) if row else None

    async def list_agents(self, level: int = None, department: str = None,
                         status: str = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List agents with filters"""
        query = "SELECT * FROM agents WHERE 1=1"
        params = []
        param_idx = 1

        if level is not None:
            query += f" AND level = ${param_idx}"
            params.append(level)
            param_idx += 1

        if department:
            query += f" AND department = ${param_idx}"
            params.append(department)
            param_idx += 1

        if status:
            query += f" AND status = ${param_idx}"
            params.append(status)
            param_idx += 1

        query += f" ORDER BY level, id LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    async def get_hierarchy(self, root_id: str = "M-001") -> Dict:
        """Get full hierarchy tree from root"""
        return await self._build_tree(root_id)

    async def _build_tree(self, agent_id: str) -> Dict:
        """Recursively build agent tree"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return {}

        children = await db.fetch("SELECT id FROM agents WHERE parent_id = $1 ORDER BY id", agent_id)
        agent["children"] = [await self._build_tree(child["id"]) for child in children]
        return agent

    async def get_department_agents(self, department: str) -> List[Dict]:
        """Get all agents in a department"""
        rows = await db.fetch("SELECT * FROM agents WHERE department = $1 ORDER BY level, id", department)
        return [dict(row) for row in rows]

    async def get_agent_stats(self) -> Dict:
        """Get agent statistics"""
        stats = await db.fetchrow("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE level = 0) as master,
                COUNT(*) FILTER (WHERE level = 1) as principals,
                COUNT(*) FILTER (WHERE level = 2) as heads,
                COUNT(*) FILTER (WHERE level = 3) as team_leaders,
                COUNT(*) FILTER (WHERE level = 4) as workers,
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COUNT(*) FILTER (WHERE status = 'idle') as idle,
                COUNT(*) FILTER (WHERE status = 'paused') as paused,
                COUNT(*) FILTER (WHERE status = 'error') as error
            FROM agents
        """)
        return dict(stats) if stats else {}

    async def pause_agent(self, agent_id: str) -> bool:
        """Pause an agent"""
        result = await db.execute("UPDATE agents SET status = 'paused' WHERE id = $1", agent_id)
        return result != "UPDATE 0"

    async def resume_agent(self, agent_id: str) -> bool:
        """Resume an agent"""
        result = await db.execute("UPDATE agents SET status = 'idle' WHERE id = $1", agent_id)
        return result != "UPDATE 0"

    async def update_agent_config(self, agent_id: str, config: Dict) -> bool:
        """Update agent configuration"""
        updates = []
        params = [agent_id]
        param_idx = 2

        allowed_fields = ["system_prompt", "model_id", "tools", "skills", "permissions", "memory_config"]
        for field in allowed_fields:
            if field in config:
                updates.append(f"{field} = ${param_idx}")
                params.append(json.dumps(config[field]) if isinstance(config[field], (dict, list)) else config[field])
                param_idx += 1

        if not updates:
            return False

        updates.append("updated_at = NOW()")
        query = f"UPDATE agents SET {', '.join(updates)} WHERE id = $1"
        result = await db.execute(query, *params)
        return result != "UPDATE 0"

    async def search_agents(self, query: str, limit: int = 50) -> List[Dict]:
        """Search agents by name, role, or department"""
        rows = await db.fetch("""
            SELECT * FROM agents
            WHERE name ILIKE $1 OR role ILIKE $1 OR department ILIKE $1
            ORDER BY level, id
            LIMIT $2
        """, f"%{query}%", limit)
        return [dict(row) for row in rows]


registry = AgentRegistry()