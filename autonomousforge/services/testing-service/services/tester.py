"""
Testing Service - Test execution and reporting
"""
import asyncio
import logging
import tempfile
import os
import subprocess
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4, UUID

from ..database import db
from ..config import settings

logger = logging.getLogger(__name__)


class Tester:
    def __init__(self):
        self._semaphore: Optional[asyncio.Semaphore] = None
        self.running_tests: Dict[str, asyncio.Task] = {}

    async def initialize(self):
        """Initialize tester"""
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_tests)
        logger.info("Testing service initialized")

    async def shutdown(self):
        """Shutdown tester"""
        for task in self.running_tests.values():
            task.cancel()
        await asyncio.gather(*self.running_tests.values(), return_exceptions=True)
        logger.info("Testing service shut down")

    # ==================== Test Suites ====================

    async def create_test_suite(self, suite_data: Dict) -> Dict:
        """Create a test suite"""
        suite_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO test_suites (id, project_id, name, description, test_type,
                                    configuration, environment, schedule, is_enabled, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """, suite_id, suite_data["project_id"], suite_data["name"], suite_data.get("description"),
            suite_data["test_type"], json.dumps(suite_data.get("configuration", {})),
            json.dumps(suite_data.get("environment", {})), suite_data.get("schedule"), True, now, now)

        return await self.get_test_suite(suite_id)

    async def get_test_suite(self, suite_id: str) -> Optional[Dict]:
        """Get test suite by ID"""
        row = await db.fetchrow("SELECT * FROM test_suites WHERE id = $1", suite_id)
        return dict(row) if row else None

    async def update_test_suite(self, suite_id: str, updates: Dict) -> Optional[Dict]:
        """Update test suite"""
        if not updates:
            return await self.get_test_suite(suite_id)

        set_clauses = []
        params = [suite_id]
        param_idx = 2

        for key, value in updates.items():
            if key in ("name", "description", "schedule"):
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
            elif key in ("configuration", "environment"):
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(json.dumps(value))
            elif key == "is_enabled":
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
            param_idx += 1

        if not set_clauses:
            return await self.get_test_suite(suite_id)

        set_clauses.append("updated_at = NOW()")
        query = f"UPDATE test_suites SET {', '.join(set_clauses)} WHERE id = $1"
        await db.execute(query, *params)
        return await self.get_test_suite(suite_id)

    async def delete_test_suite(self, suite_id: str) -> bool:
        """Delete test suite"""
        result = await db.execute("DELETE FROM test_suites WHERE id = $1", suite_id)
        return result != "DELETE 0"

    async def list_test_suites(self, project_id: str = None, test_type: str = None,
                               is_enabled: bool = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List test suites"""
        query = "SELECT * FROM test_suites WHERE 1=1"
        params = []
        param_idx = 1

        if project_id:
            query += f" AND project_id = ${param_idx}"
            params.append(project_id)
            param_idx += 1

        if test_type:
            query += f" AND test_type = ${param_idx}"
            params.append(test_type)
            param_idx += 1

        if is_enabled is not None:
            query += f" AND is_enabled = ${param_idx}"
            params.append(is_enabled)
            param_idx += 1

        query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    # ==================== Test Cases ====================

    async def create_test_case(self, case_data: Dict) -> Dict:
        """Create a test case"""
        case_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO test_cases (id, suite_id, name, description, test_code,
                                   dependencies, tags, timeout_seconds, retries, is_flaky, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """, case_id, case_data["suite_id"], case_data["name"], case_data.get("description"),
            case_data["test_code"], json.dumps(case_data.get("dependencies", [])),
            json.dumps(case_data.get("tags", [])), case_data.get("timeout_seconds", 60),
            case_data.get("retries", 0), case_data.get("is_flaky", False), now, now)

        return await self.get_test_case(case_id)

    async def get_test_case(self, case_id: str) -> Optional[Dict]:
        """Get test case by ID"""
        row = await db.fetchrow("SELECT * FROM test_cases WHERE id = $1", case_id)
        return dict(row) if row else None

    async def update_test_case(self, case_id: str, updates: Dict) -> Optional[Dict]:
        """Update test case"""
        if not updates:
            return await self.get_test_case(case_id)

        set_clauses = []
        params = [case_id]
        param_idx = 2

        for key, value in updates.items():
            if key in ("name", "description", "test_code"):
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
            elif key in ("dependencies", "tags"):
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(json.dumps(value))
            elif key in ("timeout_seconds", "retries", "is_flaky"):
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
            param_idx += 1

        if not set_clauses:
            return await self.get_test_case(case_id)

        set_clauses.append("updated_at = NOW()")
        query = f"UPDATE test_cases SET {', '.join(set_clauses)} WHERE id = $1"
        await db.execute(query, *params)
        return await self.get_test_case(case_id)

    async def delete_test_case(self, case_id: str) -> bool:
        """Delete test case"""
        result = await db.execute("DELETE FROM test_cases WHERE id = $1", case_id)
        return result != "DELETE 0"

    async def list_test_cases(self, suite_id: str = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List test cases"""
        query = "SELECT * FROM test_cases WHERE 1=1"
        params = []
        param_idx = 1

        if suite_id:
            query += f" AND suite_id = ${param_idx}"
            params.append(suite_id)
            param_idx += 1

        query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    # ==================== Test Runs ====================

    async def create_test_run(self, run_data: Dict) -> Dict:
        """Create and run a test"""
        run_id = str(uuid4())
        now = datetime.utcnow()

        suite_id = run_data["suite_id"]
        trigger_type = run_data.get("trigger_type", "manual")
        trigger_data = run_data.get("trigger_data", {})
        environment = run_data.get("environment", {})
        selected_cases = run_data.get("selected_cases")

        # Get suite info
        suite = await self.get_test_suite(suite_id)
        if not suite:
            raise ValueError("Test suite not found")

        # Get test cases to run
        if selected_cases:
            cases = await db.fetch("SELECT * FROM test_cases WHERE id = ANY($1)", selected_cases)
        else:
            cases = await db.fetch("SELECT * FROM test_cases WHERE suite_id = $1", suite_id)

        total_cases = len(cases)

        await db.execute("""
            INSERT INTO test_runs (id, suite_id, trigger_type, trigger_data, environment,
                                  status, current_case, progress, total_cases, passed, failed, skipped, errored,
                                  duration_ms, queued_at, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
        """, run_id, suite_id, trigger_type, json.dumps(trigger_data), json.dumps(environment),
            "pending", None, 0, total_cases, 0, 0, 0, 0, 0, now, now, now)

        # Run tests asynchronously
        task = asyncio.create_task(self._run_test_suite(run_id, suite, cases, environment, selected_cases))
        self.running_tests[run_id] = task

        return await self.get_test_run(run_id)

    async def get_test_run(self, run_id: str) -> Optional[Dict]:
        """Get test run by ID"""
        row = await db.fetchrow("SELECT * FROM test_runs WHERE id = $1", run_id)
        return dict(row) if row else None

    async def update_test_run(self, run_id: str, updates: Dict) -> Optional[Dict]:
        """Update test run"""
        if not updates:
            return await self.get_test_run(run_id)

        set_clauses = []
        params = [run_id]
        param_idx = 2

        for key, value in updates.items():
            if key in ("status", "current_case"):
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
            elif key == "progress":
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
            param_idx += 1

        if not set_clauses:
            return await self.get_test_run(run_id)

        set_clauses.append("updated_at = NOW()")
        query = f"UPDATE test_runs SET {', '.join(set_clauses)} WHERE id = $1"
        await db.execute(query, *params)
        return await self.get_test_run(run_id)

    async def list_test_runs(self, suite_id: str = None, status: str = None,
                            trigger_type: str = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List test runs"""
        query = "SELECT * FROM test_runs WHERE 1=1"
        params = []
        param_idx = 1

        if suite_id:
            query += f" AND suite_id = ${param_idx}"
            params.append(suite_id)
            param_idx += 1

        if status:
            query += f" AND status = ${param_idx}"
            params.append(status)
            param_idx += 1

        if trigger_type:
            query += f" AND trigger_type = ${param_idx}"
            params.append(trigger_type)
            param_idx += 1

        query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    async def cancel_test_run(self, run_id: str) -> bool:
        """Cancel a running test"""
        task = self.running_tests.get(run_id)
        if task:
            task.cancel()
            await self._update_test_run(run_id, "cancelled", "{}", "Test cancelled by user")
            return True
        return False

    # ==================== Test Results ====================

    async def create_test_result(self, result_data: Dict) -> Dict:
        """Create a test result"""
        result_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO test_results (id, run_id, case_id, status, duration_ms, output,
                                     error_message, stack_trace, assertions, coverage, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """, result_id, result_data["run_id"], result_data["case_id"], result_data["status"],
            result_data["duration_ms"], result_data.get("output"), result_data.get("error_message"),
            result_data.get("stack_trace"), json.dumps(result_data.get("assertions", [])),
            json.dumps(result_data.get("coverage")), now)

        return await self.get_test_result(result_id)

    async def get_test_result(self, result_id: str) -> Optional[Dict]:
        """Get test result by ID"""
        row = await db.fetchrow("SELECT * FROM test_results WHERE id = $1", result_id)
        return dict(row) if row else None

    async def get_test_results(self, run_id: str) -> List[Dict]:
        """Get all test results for a run"""
        rows = await db.fetch("SELECT * FROM test_results WHERE run_id = $1 ORDER BY created_at", run_id)
        return [dict(row) for row in rows]

    # ==================== Stats ====================

    async def get_stats(self, project_id: str = None) -> Dict:
        """Get testing statistics"""
        where_clause = ""
        params = []

        if project_id:
            where_clause = "WHERE project_id = $1"
            params.append(project_id)

        total_suites = await db.fetchval(f"SELECT COUNT(*) FROM test_suites {where_clause}", *params)

        if project_id:
            total_cases = await db.fetchval("""
                SELECT COUNT(*) FROM test_cases tc
                JOIN test_suites ts ON tc.suite_id = ts.id
                WHERE ts.project_id = $1
            """, project_id)
            total_runs = await db.fetchval("""
                SELECT COUNT(*) FROM test_runs tr
                JOIN test_suites ts ON tr.suite_id = ts.id
                WHERE ts.project_id = $1
            """, project_id)
        else:
            total_cases = await db.fetchval("SELECT COUNT(*) FROM test_cases")
            total_runs = await db.fetchval("SELECT COUNT(*) FROM test_runs")

        runs_by_status = await db.fetch("""
            SELECT status, COUNT(*) as count FROM test_runs
            """ + (where_clause.replace("project_id", "ts.project_id") if project_id else "") + """
            GROUP BY status
        """, *params)

        runs_by_status_dict = {row["status"]: row["count"] for row in runs_by_status}

        avg_duration = await db.fetchval("""
            SELECT AVG(duration_ms) FROM test_runs WHERE duration_ms > 0
        """) or 0

        pass_rate = 0.0
        total_completed = runs_by_status_dict.get("completed", 0)
        total_failed = runs_by_status_dict.get("failed", 0)
        if total_completed + total_failed > 0:
            pass_rate = total_completed / (total_completed + total_failed)

        flaky_cases = await db.fetchval("SELECT COUNT(*) FROM test_cases WHERE is_flaky = true")

        return {
            "total_suites": total_suites,
            "total_cases": total_cases,
            "total_runs": total_runs,
            "runs_by_status": runs_by_status_dict,
            "avg_duration_ms": int(avg_duration),
            "pass_rate": pass_rate,
            "flaky_cases": flaky_cases
        }

    async def _run_test_suite(self, test_run_id: str, test_type: str, test_path: str,
                             config: Dict, environment: Dict):
        """Run test suite"""
        await self._update_test_run(test_run_id, "running", "{}", "")

        start_time = datetime.utcnow()

        try:
            if test_type == "unit":
                result = await self._run_unit_tests(test_run_id, test_path, config, environment)
            elif test_type == "integration":
                result = await self._run_integration_tests(test_run_id, test_path, config, environment)
            elif test_type == "e2e":
                result = await self._run_e2e_tests(test_run_id, test_path, config, environment)
            elif test_type == "performance":
                result = await self._run_performance_tests(test_run_id, test_path, config, environment)
            else:
                raise ValueError(f"Unknown test type: {test_type}")

            end_time = datetime.utcnow()
            duration = int((end_time - start_time).total_seconds())

            result["duration_seconds"] = duration
            result["completed_at"] = end_time.isoformat()

            await self._update_test_run(test_run_id, "completed", json.dumps(result), "")

        except Exception as e:
            end_time = datetime.utcnow()
            duration = int((end_time - start_time).total_seconds())

            error_result = {
                "error": str(e),
                "duration_seconds": duration,
                "completed_at": end_time.isoformat(),
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }

            await self._update_test_run(test_run_id, "failed", json.dumps(error_result), str(e))

    async def _run_unit_tests(self, test_run_id: str, test_path: str,
                             config: Dict, environment: Dict) -> Dict:
        """Run unit tests (pytest)"""
        runner = config.get("runner", settings.default_test_runner)
        args = config.get("args", ["-v", "--tb=short"])

        if runner == "pytest":
            cmd = ["python", "-m", "pytest"] + args
        elif runner == "jest":
            cmd = ["npx", "jest"] + args
        elif runner == "vitest":
            cmd = ["npx", "vitest", "run"] + args
        else:
            cmd = [runner] + args

        if test_path:
            cmd.append(test_path)

        return await self._run_test_command(test_run_id, cmd, environment)

    async def _run_integration_tests(self, test_run_id: str, test_path: str,
                                    config: Dict, environment: Dict) -> Dict:
        """Run integration tests"""
        # Integration tests might need services running
        # For now, use same runner but different path/markers
        config = config.copy()
        if "args" not in config:
            config["args"] = ["-v", "--tb=short", "-m", "integration"]
        return await self._run_unit_tests(test_run_id, test_path, config, environment)

    async def _run_e2e_tests(self, test_run_id: str, test_path: str,
                            config: Dict, environment: Dict) -> Dict:
        """Run end-to-end tests"""
        runner = config.get("runner", "playwright")
        args = config.get("args", [])

        if runner == "playwright":
            cmd = ["npx", "playwright", "test"] + args
        elif runner == "cypress":
            cmd = ["npx", "cypress", "run"] + args
        else:
            cmd = [runner] + args

        if test_path:
            cmd.append(test_path)

        return await self._run_test_command(test_run_id, cmd, environment)

    async def _run_performance_tests(self, test_run_id: str, test_path: str,
                                    config: Dict, environment: Dict) -> Dict:
        """Run performance tests"""
        runner = config.get("runner", "locust")
        args = config.get("args", [])

        if runner == "locust":
            cmd = ["locust", "--headless"] + args
        elif runner == "k6":
            cmd = ["k6", "run"] + args
        else:
            cmd = [runner] + args

        if test_path:
            cmd.append(test_path)

        return await self._run_test_command(test_run_id, cmd, environment)

    async def _run_test_command(self, test_run_id: str, cmd: List[str],
                               environment: Dict) -> Dict:
        """Run test command and parse results"""
        working_dir = environment.get("working_dir", "/workspace")
        env = {**os.environ, **environment}

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env
        )

        output_lines = []
        async for line in process.stdout:
            line_str = line.decode('utf-8', errors='replace').rstrip()
            output_lines.append(line_str)

            # Periodically update logs
            if len(output_lines) % 20 == 0:
                await self._update_test_run_logs(test_run_id, "\n".join(output_lines))

        await process.wait()

        # Parse results based on test runner
        output = "\n".join(output_lines)
        result = self._parse_test_output(cmd[0], output, process.returncode)
        result["raw_output"] = output
        result["exit_code"] = process.returncode

        return result

    def _parse_test_output(self, runner: str, output: str, exit_code: int) -> Dict:
        """Parse test output to extract results"""
        # Default parsing
        result = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0,
            "exit_code": exit_code
        }

        # Pytest parsing
        if "pytest" in runner:
            import re
            # Look for pattern: "X passed, Y failed, Z skipped"
            match = re.search(r'(\d+) passed', output)
            if match:
                result["passed"] = int(match.group(1))
            match = re.search(r'(\d+) failed', output)
            if match:
                result["failed"] = int(match.group(1))
            match = re.search(r'(\d+) skipped', output)
            if match:
                result["skipped"] = int(match.group(1))

        # Jest parsing
        elif "jest" in runner:
            import re
            match = re.search(r'Tests:\s+(\d+)\s+passed', output)
            if match:
                result["passed"] = int(match.group(1))
            match = re.search(r'Tests:\s+(\d+)\s+failed', output)
            if match:
                result["failed"] = int(match.group(1))

        result["total"] = result["passed"] + result["failed"] + result["skipped"]
        return result

    async def _update_test_run(self, test_run_id: str, status: str,
                              results: str, logs: str):
        """Update test run record"""
        updates = ["status = $2", "results = $3", "logs = $4", "updated_at = NOW()"]
        params = [test_run_id, status, results, logs]

        if status in ("completed", "failed"):
            updates.append("completed_at = NOW()")

        query = f"UPDATE test_runs SET {', '.join(updates)} WHERE id = $1"
        await db.execute(query, *params)

    async def _update_test_run_logs(self, test_run_id: str, logs: str):
        """Update test run logs"""
        await db.execute(
            "UPDATE test_runs SET logs = $1, updated_at = NOW() WHERE id = $2",
            logs, test_run_id
        )

    tester = Tester()