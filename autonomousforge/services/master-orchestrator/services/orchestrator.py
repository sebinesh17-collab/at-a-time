"""
Master Orchestrator Service - Core orchestration logic
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import json
import httpx

from ..database import db
from ..config import settings


class MasterOrchestrator:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.http_client.aclose()

    # ==================== Project Management ====================

    async def create_project(self, owner_id: UUID, name: str, description: str,
                            project_type: str, tech_stack: List[str] = None) -> Dict[str, Any]:
        """Create a new project"""
        project_id = uuid4()
        await db.execute("""
            INSERT INTO projects (id, name, description, project_type, tech_stack, owner_id, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'planning')
        """, project_id, name, description, project_type, tech_stack or [], owner_id)

        # Create initial conversation for project
        conv_id = uuid4()
        await db.execute("""
            INSERT INTO conversations (id, project_id, owner_id, title, mode)
            VALUES ($1, $2, $3, $4, 'chat')
        """, conv_id, project_id, owner_id, f"{name} - Discussion")

        return {"id": str(project_id), "conversation_id": str(conv_id)}

    async def get_project(self, project_id: UUID, owner_id: UUID) -> Optional[Dict]:
        """Get project by ID"""
        row = await db.fetchrow("""
            SELECT * FROM projects WHERE id = $1 AND owner_id = $2
        """, project_id, owner_id)
        return dict(row) if row else None

    async def list_projects(self, owner_id: UUID, status: str = None) -> List[Dict]:
        """List projects for owner"""
        query = "SELECT * FROM projects WHERE owner_id = $1"
        params = [owner_id]
        if status:
            query += " AND status = $2"
            params.append(status)
        query += " ORDER BY updated_at DESC"
        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    async def update_project_status(self, project_id: UUID, owner_id: UUID, status: str) -> bool:
        """Update project status"""
        result = await db.execute("""
            UPDATE projects SET status = $1, updated_at = NOW()
            WHERE id = $2 AND owner_id = $3
        """, status, project_id, owner_id)
        return result != "UPDATE 0"

    # ==================== Task Decomposition ====================

    async def decompose_project(self, project_id: UUID, owner_id: UUID,
                               requirements: str) -> List[Dict[str, Any]]:
        """
        Decompose project into hierarchical tasks:
        Project -> Epic -> Feature -> Task -> Subtask -> Microtask -> Atomic
        """
        # This would typically call the model gateway to analyze requirements
        # For now, create a basic task structure
        tasks = []

        # Create Epic
        epic_id = uuid4()
        await db.execute("""
            INSERT INTO tasks (id, project_id, title, description, task_type, priority, status, expected_output)
            VALUES ($1, $2, $3, $4, 'epic', 100, 'pending', $5)
        """, epic_id, project_id, f"Epic: {requirements[:100]}", requirements,
            {"deliverable": "Complete project implementation"})

        tasks.append({
            "id": str(epic_id),
            "type": "epic",
            "title": f"Epic: {requirements[:100]}",
            "children": []
        })

        # Create standard features for any project
        features = [
            ("Project Setup & Architecture", "Initialize project structure, configuration, and core architecture"),
            ("Core Implementation", "Implement main functionality and business logic"),
            ("Testing & Quality Assurance", "Write tests, perform code review, ensure quality"),
            ("Documentation & Deployment", "Create documentation, configure deployment"),
        ]

        for i, (title, desc) in enumerate(features):
            feature_id = uuid4()
            await db.execute("""
                INSERT INTO tasks (id, project_id, parent_task_id, title, description, task_type, priority, status)
                VALUES ($1, $2, $3, $4, $5, 'feature', $6, 'pending')
            """, feature_id, project_id, epic_id, title, desc, 80 - i * 10)

            feature_task = {
                "id": str(feature_id),
                "type": "feature",
                "title": title,
                "children": []
            }
            tasks[0]["children"].append(feature_task)

            # Add tasks for each feature
            task_templates = self._get_task_templates(title)
            for j, (task_title, task_desc) in enumerate(task_templates):
                task_id = uuid4()
                await db.execute("""
                    INSERT INTO tasks (id, project_id, parent_task_id, title, description, task_type, priority, status)
                    VALUES ($1, $2, $3, $4, $5, 'task', $6, 'pending')
                """, task_id, project_id, feature_id, task_title, task_desc, 60 - j * 5)

                feature_task["children"].append({
                    "id": str(task_id),
                    "type": "task",
                    "title": task_title,
                    "children": []
                })

        return tasks

    def _get_task_templates(self, feature_title: str) -> List[tuple]:
        """Get task templates based on feature type"""
        templates = {
            "Project Setup & Architecture": [
                ("Initialize repository & configuration", "Set up git, config files, CI/CD"),
                ("Define database schema", "Create database models and migrations"),
                ("Set up development environment", "Configure Docker, local dev setup"),
                ("Create core module structure", "Define package/module architecture"),
            ],
            "Core Implementation": [
                ("Implement data models", "Create core data structures and ORM models"),
                ("Build API endpoints", "Create REST/gRPC endpoints"),
                ("Implement business logic", "Core application logic and services"),
                ("Add authentication/authorization", "Secure the application"),
            ],
            "Testing & Quality Assurance": [
                ("Write unit tests", "Test individual components"),
                ("Write integration tests", "Test component interactions"),
                ("Perform code review", "Review code quality and standards"),
                ("Run security audit", "Check for vulnerabilities"),
            ],
            "Documentation & Deployment": [
                ("Write API documentation", "Document all endpoints"),
                ("Create user guides", "End-user documentation"),
                ("Configure production deployment", "Set up staging/production"),
                ("Set up monitoring & alerting", "Observability stack"),
            ],
        }
        return templates.get(feature_title, [
            ("Analyze requirements", "Break down and analyze feature requirements"),
            ("Design solution", "Create technical design"),
            ("Implement solution", "Write code"),
            ("Test & validate", "Verify implementation"),
        ])

    async def get_task_tree(self, project_id: UUID) -> List[Dict]:
        """Get full task hierarchy for project"""
        rows = await db.fetch("""
            SELECT * FROM tasks WHERE project_id = $1 ORDER BY task_type, priority DESC, created_at
        """, project_id)

        # Build tree
        task_map = {row["id"]: {**dict(row), "children": []} for row in rows}
        roots = []

        for task in task_map.values():
            parent_id = task["parent_task_id"]
            if parent_id and parent_id in task_map:
                task_map[parent_id]["children"].append(task)
            else:
                roots.append(task)

        return roots

    # ==================== Agent Coordination ====================

    async def assign_task_to_agent(self, task_id: UUID, agent_id: str) -> bool:
        """Assign task to specific agent"""
        result = await db.execute("""
            UPDATE tasks SET assigned_agent_id = $1, status = 'queued', queued_at = NOW()
            WHERE id = $2 AND status = 'pending'
        """, agent_id, task_id)
        return result != "UPDATE 0"

    async def get_available_agents(self, level: int = None, department: str = None) -> List[Dict]:
        """Get available agents for task assignment"""
        query = "SELECT * FROM agents WHERE status = 'idle'"
        params = []

        if level is not None:
            query += " AND level = $1"
            params.append(level)

        if department:
            idx = len(params) + 1
            query += f" AND department = ${idx}"
            params.append(department)

        query += " ORDER BY tasks_completed ASC LIMIT 10"
        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    async def send_agent_message(self, project_id: UUID, task_id: UUID,
                                sender_id: str, recipient_id: str,
                                message_type: str, content: Dict) -> UUID:
        """Send message between agents"""
        msg_id = uuid4()
        await db.execute("""
            INSERT INTO messages (id, project_id, task_id, sender_id, recipient_id, message_type, content)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, msg_id, project_id, task_id, sender_id, recipient_id, message_type, content)
        return msg_id

    # ==================== Model Gateway Integration ====================

    async def call_model(self, model_id: str, prompt: str, context: Dict = None,
                        tools: List[str] = None) -> Dict[str, Any]:
        """Call model through model gateway"""
        try:
            response = await self.http_client.post(
                f"{settings.model_gateway_url}/api/models/complete",
                json={
                    "model": model_id,
                    "prompt": prompt,
                    "context": context or {},
                    "tools": tools or [],
                },
                timeout=60.0
            )
            return response.json()
        except Exception as e:
            return {"error": str(e), "success": False}

    # ==================== Execution Coordination ====================

    async def execute_task(self, task_id: UUID, agent_id: str) -> Dict[str, Any]:
        """Execute a task by an agent"""
        # Get task details
        task = await db.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)
        if not task:
            return {"success": False, "error": "Task not found"}

        # Get agent details
        agent = await db.fetchrow("SELECT * FROM agents WHERE id = $1", agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}

        # Update task status
        await db.execute("""
            UPDATE tasks SET status = 'running', started_at = NOW(), assigned_agent_id = $1
            WHERE id = $2
        """, agent_id, task_id)

        # Update agent status
        await db.execute("""
            UPDATE agents SET status = 'active', current_task_id = $1, last_active_at = NOW()
            WHERE id = $2
        """, task_id, agent_id)

        try:
            # Build prompt for agent
            prompt = self._build_agent_prompt(task, agent)

            # Call model
            result = await self.call_model(
                agent["model_id"] or "default",
                prompt,
                context={"task": dict(task), "agent": dict(agent)},
                tools=agent["tools"] or []
            )

            if result.get("success"):
                # Update task as completed
                await db.execute("""
                    UPDATE tasks SET status = 'completed', completed_at = NOW(), result = $1
                    WHERE id = $2
                """, result.get("output", {}), task_id)

                # Update agent stats
                await db.execute("""
                    UPDATE agents SET status = 'idle', current_task_id = NULL,
                        tasks_completed = tasks_completed + 1,
                        avg_execution_time_ms = (avg_execution_time_ms * tasks_completed + $1) / (tasks_completed + 1)
                    WHERE id = $2
                """, 0, agent_id)  # Would calculate actual time

                return {"success": True, "output": result.get("output")}
            else:
                raise Exception(result.get("error", "Model execution failed"))

        except Exception as e:
            # Handle failure
            await db.execute("""
                UPDATE tasks SET status = 'failed', error_message = $1, retry_count = retry_count + 1
                WHERE id = $2
            """, str(e), task_id)

            await db.execute("""
                UPDATE agents SET status = 'idle', current_task_id = NULL, tasks_failed = tasks_failed + 1
                WHERE id = $1
            """, agent_id)

            return {"success": False, "error": str(e)}

    def _build_agent_prompt(self, task: Dict, agent: Dict) -> str:
        """Build prompt for agent execution"""
        base_prompt = agent.get("system_prompt", "You are an expert software engineer.")

        task_prompt = f"""
{base_prompt}

TASK: {task['title']}
DESCRIPTION: {task['description'] or 'No description provided'}
TYPE: {task['task_type']}
PRIORITY: {task['priority']}

EXPECTED OUTPUT: {json.dumps(task.get('expected_output', {}), indent=2)}
ACCEPTANCE CRITERIA: {json.dumps(task.get('acceptance_criteria', {}), indent=2)}

REQUIRED SKILLS: {', '.join(task.get('required_skills', []))}
REQUIRED TOOLS: {', '.join(task.get('required_tools', []))}

Execute this task and provide the expected output in the specified format.
"""

        return task_prompt

    # ==================== Monitoring ====================

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        stats = {}

        # Agent stats
        agent_stats = await db.fetchrow("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COUNT(*) FILTER (WHERE level = 0) as master,
                COUNT(*) FILTER (WHERE level = 1) as principals,
                COUNT(*) FILTER (WHERE level = 2) as heads,
                COUNT(*) FILTER (WHERE level = 3) as team_leaders,
                COUNT(*) FILTER (WHERE level = 4) as workers
            FROM agents
        """)
        stats.update(dict(agent_stats))

        # Task stats
        task_stats = await db.fetchrow("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'running') as running,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'failed') as failed,
                COUNT(*) FILTER (WHERE status = 'pending') as pending
            FROM tasks
        """)
        stats.update(dict(task_stats))

        # Project stats
        project_stats = await db.fetchrow("""
            SELECT COUNT(*) as total FROM projects
        """)
        stats["total_projects"] = project_stats["total"] if project_stats else 0

        return stats


orchestrator = MasterOrchestrator()