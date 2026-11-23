"""
Execution Service - Code execution and sandboxing
"""
import asyncio
import logging
import tempfile
import os
import subprocess
import json
import shlex
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from ..database import db
from ..config import settings

logger = logging.getLogger(__name__)


class Executor:
    def __init__(self):
        self._semaphore: Optional[asyncio.Semaphore] = None
        self.running_executions: Dict[str, asyncio.Task] = {}

    async def initialize(self):
        """Initialize executor"""
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_executions)
        logger.info("Execution service initialized")

    async def shutdown(self):
        """Shutdown executor - cancel running executions"""
        for task in self.running_executions.values():
            task.cancel()
        await asyncio.gather(*self.running_executions.values(), return_exceptions=True)
        logger.info("Execution service shut down")

    # ==================== Execution ====================

    async def execute_code(self, execution_data: Dict) -> Dict:
        """Execute code in sandbox"""
        execution_id = str(uuid4())
        now = datetime.utcnow()

        language = execution_data.get("language", "python")
        code = execution_data.get("code", "")
        stdin = execution_data.get("stdin", "")
        timeout = min(execution_data.get("timeout", settings.execution_timeout_seconds),
                      settings.execution_timeout_seconds)

        # Validate language
        allowed = settings.allowed_languages.split(",")
        if language not in allowed:
            raise ValueError(f"Language not allowed: {language}")

        # Create execution record
        await db.execute("""
            INSERT INTO executions (id, project_id, language, code, stdin, timeout,
                                   status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, execution_id, execution_data.get("project_id"), language, code, stdin,
            timeout, "pending", now, now)

        # Execute asynchronously
        task = asyncio.create_task(self._run_execution(execution_id, language, code, stdin, timeout))
        self.running_executions[execution_id] = task

        try:
            result = await asyncio.wait_for(task, timeout=timeout + 5)
            return result
        except asyncio.TimeoutError:
            task.cancel()
            await self._update_execution(execution_id, "timeout", "", "Execution timed out")
            return await self.get_execution(execution_id)
        finally:
            self.running_executions.pop(execution_id, None)

    async def _run_execution(self, execution_id: str, language: str, code: str,
                            stdin: str, timeout: int) -> Dict:
        """Run code execution"""
        await self._update_execution(execution_id, "running", "", "")

        start_time = datetime.utcnow()

        try:
            if language == "python":
                result = await self._execute_python(code, stdin, timeout)
            elif language in ("javascript", "typescript"):
                result = await self._execute_node(code, stdin, timeout, language)
            elif language == "bash":
                result = await self._execute_bash(code, stdin, timeout)
            elif language == "sql":
                result = await self._execute_sql(code, timeout)
            else:
                raise ValueError(f"Unsupported language: {language}")

            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            await self._update_execution(
                execution_id, "completed", result["stdout"], result["stderr"],
                result["exit_code"], duration_ms
            )

            return await self.get_execution(execution_id)

        except Exception as e:
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            await self._update_execution(
                execution_id, "error", "", str(e), -1, duration_ms
            )

            return await self.get_execution(execution_id)

    async def _execute_python(self, code: str, stdin: str, timeout: int) -> Dict:
        """Execute Python code"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            process = await asyncio.create_subprocess_exec(
                'python3', temp_file,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(stdin.encode() if stdin else None),
                timeout=timeout
            )

            return {
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "exit_code": process.returncode or 0
            }
        finally:
            os.unlink(temp_file)

    async def _execute_node(self, code: str, stdin: str, timeout: int, language: str) -> Dict:
        """Execute JavaScript/TypeScript code"""
        ext = '.ts' if language == 'typescript' else '.js'
        with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            cmd = ['node'] if language == 'javascript' else ['npx', 'ts-node']
            cmd.append(temp_file)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(stdin.encode() if stdin else None),
                timeout=timeout
            )

            return {
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "exit_code": process.returncode or 0
            }
        finally:
            os.unlink(temp_file)

    async def _execute_bash(self, code: str, stdin: str, timeout: int) -> Dict:
        """Execute Bash script"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            os.chmod(temp_file, 0o755)
            process = await asyncio.create_subprocess_exec(
                'bash', temp_file,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(stdin.encode() if stdin else None),
                timeout=timeout
            )

            return {
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "exit_code": process.returncode or 0
            }
        finally:
            os.unlink(temp_file)

    async def _execute_sql(self, code: str, timeout: int) -> Dict:
        """Execute SQL query"""
        # This would connect to the database and execute
        # For now, return a placeholder
        return {
            "stdout": "SQL execution not fully implemented",
            "stderr": "",
            "exit_code": 0
        }

    async def _update_execution(self, execution_id: str, status: str, stdout: str,
                               stderr: str, exit_code: int = None, duration_ms: int = None):
        """Update execution record"""
        updates = ["status = $2", "stdout = $3", "stderr = $4", "updated_at = NOW()"]
        params = [execution_id, status, stdout, stderr]
        param_idx = 5

        if exit_code is not None:
            updates.append(f"exit_code = ${param_idx}")
            params.append(exit_code)
            param_idx += 1

        if duration_ms is not None:
            updates.append(f"duration_ms = ${param_idx}")
            params.append(duration_ms)
            param_idx += 1

        if status in ("completed", "error", "timeout"):
            updates.append(f"completed_at = NOW()")

        query = f"UPDATE executions SET {', '.join(updates)} WHERE id = $1"
        await db.execute(query, *params)

    # ==================== Query Methods ====================

    async def get_execution(self, execution_id: str) -> Optional[Dict]:
        """Get execution by ID"""
        row = await db.fetchrow("SELECT * FROM executions WHERE id = $1", execution_id)
        return dict(row) if row else None

    async def list_executions(self, project_id: str = None, status: str = None,
                             limit: int = 100, offset: int = 0) -> List[Dict]:
        """List executions"""
        query = "SELECT * FROM executions WHERE 1=1"
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

        query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        task = self.running_executions.get(execution_id)
        if task:
            task.cancel()
            await self._update_execution(execution_id, "cancelled", "", "Cancelled by user")
            return True
        return False


executor = Executor()