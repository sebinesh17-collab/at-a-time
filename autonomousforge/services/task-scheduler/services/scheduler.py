"""
Task Scheduler Service - DAG-based task decomposition and scheduling
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from ..database import db
from ..config import settings

logger = logging.getLogger(__name__)


class TaskScheduler:
    def __init__(self):
        self.running = False
        self.worker_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the scheduler worker"""
        self.running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Task scheduler worker started")

    async def stop(self):
        """Stop the scheduler worker"""
        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Task scheduler worker stopped")

    async def _worker_loop(self):
        """Main scheduler loop - polls for ready tasks"""
        while self.running:
            try:
                await self._process_ready_tasks()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
            await asyncio.sleep(settings.poll_interval_seconds)

    async def _process_ready_tasks(self):
        """Find and dispatch ready tasks"""
        # Get tasks that are ready to run (dependencies satisfied, not running)
        rows = await db.fetch("""
            SELECT t.* FROM tasks t
            WHERE t.status = 'pending'
            AND NOT EXISTS (
                SELECT 1 FROM task_dependencies td
                JOIN tasks dep ON dep.id = td.depends_on_task_id
                WHERE td.task_id = t.id
                AND dep.status != 'completed'
            )
            AND t.scheduled_at <= NOW()
            ORDER BY t.priority DESC, t.created_at ASC
            LIMIT $1
        """, settings.max_concurrent_tasks)

        for row in rows:
            task = dict(row)
            asyncio.create_task(self._execute_task(task))

    async def _execute_task(self, task: Dict):
        """Execute a single task"""
        task_id = task["id"]
        try:
            # Mark task as running
            await db.execute(
                "UPDATE tasks SET status = 'running', started_at = NOW(), updated_at = NOW() WHERE id = $1",
                task_id
            )

            # Get task details and agent assignment
            agent_id = task.get("assigned_agent_id")
            if not agent_id:
                # Auto-assign based on task type and department
                agent_id = await self._assign_agent(task)

            # Execute based on task type
            result = await self._run_task(task, agent_id)

            # Mark as completed
            await db.execute("""
                UPDATE tasks
                SET status = 'completed', completed_at = NOW(), updated_at = NOW(),
                    result = $1, output = $2
                WHERE id = $3
            """, json.dumps(result), result.get("output", ""), task_id)

            # Check dependent tasks
            await self._check_dependent_tasks(task_id)

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            await db.execute("""
                UPDATE tasks
                SET status = 'failed', completed_at = NOW(), updated_at = NOW(),
                    error = $1
                WHERE id = $2
            """, str(e), task_id)

    async def _assign_agent(self, task: Dict) -> str:
        """Auto-assign best agent for task"""
        task_type = task.get("task_type", "implementation")
        department = task.get("department", "General")

        # Find available agent in department
        row = await db.fetchrow("""
            SELECT id FROM agents
            WHERE department = $1 AND status = 'idle' AND level >= 3
            ORDER BY level ASC, RANDOM()
            LIMIT 1
        """, department)

        if row:
            agent_id = row["id"]
            await db.execute(
                "UPDATE agents SET status = 'busy', current_task_id = $1 WHERE id = $2",
                task["id"], agent_id
            )
            return agent_id

        # Fallback to any idle worker
        row = await db.fetchrow("""
            SELECT id FROM agents
            WHERE status = 'idle' AND level = 4
            ORDER BY RANDOM()
            LIMIT 1
        """)

        if row:
            agent_id = row["id"]
            await db.execute(
                "UPDATE agents SET status = 'busy', current_task_id = $1 WHERE id = $2",
                task["id"], agent_id
            )
            return agent_id

        return "M-001"  # Master as last resort

    async def _run_task(self, task: Dict, agent_id: str) -> Dict:
        """Run task via model gateway (placeholder for now)"""
        task_type = task.get("task_type", "implementation")
        payload = task.get("payload", {})

        # Simulate task execution based on type
        if task_type == "decompose":
            return await self._decompose_task(task, agent_id)
        elif task_type == "implementation":
            return await self._implement_task(task, agent_id)
        elif task_type == "review":
            return await self._review_task(task, agent_id)
        elif task_type == "test":
            return await self._test_task(task, agent_id)
        elif task_type == "integrate":
            return await self._integrate_task(task, agent_id)
        else:
            return {"status": "completed", "output": f"Task {task['id']} executed", "agent": agent_id}

    async def _decompose_task(self, task: Dict, agent_id: str) -> Dict:
        """Decompose task into subtasks using DAG logic"""
        # This would call the model gateway to decompose
        # For now, return mock decomposition
        return {
            "status": "completed",
            "output": f"Decomposed task {task['id']} into subtasks",
            "agent": agent_id,
            "subtasks_created": 0
        }

    async def _implement_task(self, task: Dict, agent_id: str) -> Dict:
        """Execute implementation task"""
        # Would call model gateway for code generation
        return {
            "status": "completed",
            "output": f"Implemented task {task['id']}",
            "agent": agent_id,
            "files_changed": []
        }

    async def _review_task(self, task: Dict, agent_id: str) -> Dict:
        """Execute code review task"""
        return {
            "status": "completed",
            "output": f"Reviewed task {task['id']}",
            "agent": agent_id,
            "approval": True
        }

    async def _test_task(self, task: Dict, agent_id: str) -> Dict:
        """Execute testing task"""
        return {
            "status": "completed",
            "output": f"Tested task {task['id']}",
            "agent": agent_id,
            "tests_passed": True
        }

    async def _integrate_task(self, task: Dict, agent_id: str) -> Dict:
        """Execute integration task"""
        return {
            "status": "completed",
            "output": f"Integrated task {task['id']}",
            "agent": agent_id
        }

    async def _check_dependent_tasks(self, completed_task_id: str):
        """Check if dependent tasks can now run"""
        # Dependencies are checked in _process_ready_tasks via SQL

    # ==================== Public API ====================

    async def create_task(self, project_id: str, task_data: Dict) -> Dict:
        """Create a new task"""
        task_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO tasks (id, project_id, parent_task_id, title, description, task_type,
                              department, priority, status, payload, assigned_agent_id,
                              scheduled_at, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        """, task_id, project_id, task_data.get("parent_task_id"),
            task_data.get("title"), task_data.get("description"),
            task_data.get("task_type", "implementation"),
            task_data.get("department", "General"),
            task_data.get("priority", 5),
            "pending",
            json.dumps(task_data.get("payload", {})),
            task_data.get("assigned_agent_id"),
            task_data.get("scheduled_at", now),
            now, now)

        # Add dependencies if specified
        for dep_id in task_data.get("dependencies", []):
            await db.execute("""
                INSERT INTO task_dependencies (task_id, depends_on_task_id)
                VALUES ($1, $2)
            """, task_id, dep_id)

        return await self.get_task(task_id)

    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID"""
        row = await db.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)
        return dict(row) if row else None

    async def list_tasks(self, project_id: str = None, status: str = None,
                         limit: int = 100, offset: int = 0) -> List[Dict]:
        """List tasks with filters"""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        param_idx = 1

        if project_id:
            query += f" AND project_id = ${param_idx}"
            params.append(project_id)
            param_idx += 1

        if status:
            query += f" AND status = ${param_idx}"
            params.append(status)
            param_idx += 1

        query += f" ORDER BY priority DESC, created_at ASC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    async def update_task(self, task_id: str, updates: Dict) -> Optional[Dict]:
        """Update task"""
        allowed = ["title", "description", "priority", "status", "payload",
                   "assigned_agent_id", "scheduled_at"]
        set_clauses = []
        params = [task_id]
        param_idx = 2

        for field in allowed:
            if field in updates:
                set_clauses.append(f"{field} = ${param_idx}")
                params.append(updates[field])
                param_idx += 1

        if not set_clauses:
            return None

        set_clauses.append("updated_at = NOW()")
        query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = $1"
        await db.execute(query, *params)
        return await self.get_task(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        result = await db.execute("""
            UPDATE tasks SET status = 'cancelled', updated_at = NOW()
            WHERE id = $1 AND status IN ('pending', 'running')
        """, task_id)
        return result != "UPDATE 0"

    async def get_task_tree(self, project_id: str) -> Dict:
        """Get full task hierarchy for a project"""
        rows = await db.fetch("""
            SELECT * FROM tasks WHERE project_id = $1 ORDER BY created_at
        """, project_id)

        tasks_by_id = {row["id"]: dict(row) for row in rows}
        for task in tasks_by_id.values():
            task["children"] = []

        root_tasks = []
        for task in tasks_by_id.values():
            parent_id = task.get("parent_task_id")
            if parent_id and parent_id in tasks_by_id:
                tasks_by_id[parent_id]["children"].append(task)
            else:
                root_tasks.append(task)

        return {"project_id": project_id, "tasks": root_tasks}

    async def decompose_project(self, project_id: str, description: str,
                                epic_titles: List[str] = None) -> List[Dict]:
        """Decompose a project into hierarchical tasks (Epic -> Feature -> Task -> Subtask -> Microtask -> Atomic)"""
        # This would use the master orchestrator to do LLM-based decomposition
        # For now, create a basic structure
        created_tasks = []

        # Create epics
        epics = epic_titles or ["Research & Planning", "Architecture & Design",
                                 "Core Implementation", "Testing & QA",
                                 "Documentation & Deployment"]

        for i, epic_title in enumerate(epics):
            epic = await self.create_task(project_id, {
                "title": epic_title,
                "description": f"Epic: {epic_title}",
                "task_type": "decompose",
                "department": "System Architecture and Planning",
                "priority": 10 - i,
                "payload": {"level": "epic", "order": i}
            })
            created_tasks.append(epic)

            # Create features for each epic (2-3 per epic)
            for j in range(2):
                feature = await self.create_task(project_id, {
                    "parent_task_id": epic["id"],
                    "title": f"{epic_title} - Feature {j+1}",
                    "description": f"Feature {j+1} of {epic_title}",
                    "task_type": "decompose",
                    "department": "System Architecture and Planning",
                    "priority": 8 - i,
                    "payload": {"level": "feature", "epic_order": i, "feature_order": j},
                    "dependencies": [epic["id"]]
                })
                created_tasks.append(feature)

        return created_tasks


scheduler = TaskScheduler()