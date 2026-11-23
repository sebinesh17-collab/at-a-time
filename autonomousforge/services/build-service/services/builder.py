"""
Build Service - Project building and packaging
"""
import asyncio
import logging
import tempfile
import os
import shutil
import subprocess
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
from pathlib import Path

from ..database import db
from ..config import settings

logger = logging.getLogger(__name__)


class Builder:
    def __init__(self):
        self._semaphore: Optional[asyncio.Semaphore] = None
        self.running_builds: Dict[str, asyncio.Task] = {}
        self.cache_dir = Path(settings.build_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Initialize builder"""
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_builds)
        logger.info("Build service initialized")

    async def shutdown(self):
        """Shutdown builder"""
        for task in self.running_builds.values():
            task.cancel()
        await asyncio.gather(*self.running_builds.values(), return_exceptions=True)
        logger.info("Build service shut down")

    # ==================== Build Operations ====================

    async def start_build(self, build_data: Dict) -> Dict:
        """Start a new build"""
        build_id = str(uuid4())
        now = datetime.utcnow()

        project_id = build_data.get("project_id")
        build_type = build_data.get("build_type", "docker")  # docker, npm, python, custom
        config = build_data.get("config", {})
        source_path = build_data.get("source_path")
        environment = build_data.get("environment", {})

        await db.execute("""
            INSERT INTO builds (id, project_id, build_type, config, source_path,
                               environment, status, logs, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, build_id, project_id, build_type, json.dumps(config), source_path,
            json.dumps(environment), "pending", "", now, now)

        # Start build asynchronously
        task = asyncio.create_task(self._run_build(build_id, build_type, config, source_path, environment))
        self.running_builds[build_id] = task

        return await self.get_build(build_id)

    async def _run_build(self, build_id: str, build_type: str, config: Dict,
                        source_path: str, environment: Dict):
        """Run build process"""
        await self._update_build(build_id, "running", "Build started\n")

        start_time = datetime.utcnow()
        logs = []

        def log(message: str):
            logs.append(f"[{datetime.utcnow().isoformat()}] {message}")
            # Update logs periodically
            if len(logs) % 10 == 0:
                asyncio.create_task(self._update_build_logs(build_id, "\n".join(logs)))

        try:
            if build_type == "docker":
                result = await self._build_docker(build_id, config, source_path, environment, log)
            elif build_type == "npm":
                result = await self._build_npm(build_id, config, source_path, environment, log)
            elif build_type == "python":
                result = await self._build_python(build_id, config, source_path, environment, log)
            elif build_type == "custom":
                result = await self._build_custom(build_id, config, source_path, environment, log)
            else:
                raise ValueError(f"Unknown build type: {build_type}")

            end_time = datetime.utcnow()
            duration = int((end_time - start_time).total_seconds())

            final_logs = "\n".join(logs) + f"\nBuild completed in {duration}s"
            await self._update_build(build_id, "completed", final_logs, result.get("artifact_path"), duration)
            await self._update_build_logs(build_id, final_logs)

        except Exception as e:
            end_time = datetime.utcnow()
            duration = int((end_time - start_time).total_seconds())

            error_logs = "\n".join(logs) + f"\nBuild failed: {str(e)}"
            await self._update_build(build_id, "failed", error_logs, None, duration)
            await self._update_build_logs(build_id, error_logs)

    async def _build_docker(self, build_id: str, config: Dict, source_path: str,
                           environment: Dict, log) -> Dict:
        """Build Docker image"""
        if not settings.docker_enabled:
            raise Exception("Docker builds not enabled")

        dockerfile = config.get("dockerfile", "Dockerfile")
        tag = config.get("tag", f"autonomousforge/build-{build_id[:8]}")
        build_args = config.get("build_args", {})

        # Prepare build context
        if source_path and os.path.exists(source_path):
            context_dir = source_path
        else:
            # Create temporary context
            context_dir = tempfile.mkdtemp(prefix=f"build-{build_id}-")

        try:
            log(f"Building Docker image: {tag}")
            log(f"Context: {context_dir}")
            log(f"Dockerfile: {dockerfile}")

            # Build command
            cmd = ["docker", "build", "-t", tag, "-f", dockerfile]

            for key, value in build_args.items():
                cmd.extend(["--build-arg", f"{key}={value}"])

            cmd.append(context_dir)

            # Run build
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env={**os.environ, **environment}
            )

            async for line in process.stdout:
                log(line.decode('utf-8', errors='replace').rstrip())

            await process.wait()

            if process.returncode != 0:
                raise Exception(f"Docker build failed with exit code {process.returncode}")

            log(f"Docker image built successfully: {tag}")

            # Optionally push to registry
            if config.get("push", False):
                registry = config.get("registry", "")
                push_tag = f"{registry}/{tag}" if registry else tag
                log(f"Pushing to registry: {push_tag}")

                push_process = await asyncio.create_subprocess_exec(
                    "docker", "push", push_tag,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )

                async for line in push_process.stdout:
                    log(line.decode('utf-8', errors='replace').rstrip())

                await push_process.wait()

                if push_process.returncode != 0:
                    raise Exception("Docker push failed")

                log("Push completed")

            return {"artifact_path": tag, "type": "docker_image"}

        finally:
            if not source_path and os.path.exists(context_dir):
                shutil.rmtree(context_dir, ignore_errors=True)

    async def _build_npm(self, build_id: str, config: Dict, source_path: str,
                        environment: Dict, log) -> Dict:
        """Build NPM project"""
        if not source_path or not os.path.exists(source_path):
            raise Exception("Source path required for NPM build")

        package_json = os.path.join(source_path, "package.json")
        if not os.path.exists(package_json):
            raise Exception("package.json not found")

        log(f"Building NPM project: {source_path}")

        # Install dependencies
        log("Installing dependencies...")
        install_cmd = config.get("install_command", "npm ci")
        process = await asyncio.create_subprocess_shell(
            install_cmd,
            cwd=source_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env={**os.environ, **environment}
        )

        async for line in process.stdout:
            log(line.decode('utf-8', errors='replace').rstrip())

        await process.wait()
        if process.returncode != 0:
            raise Exception("NPM install failed")

        # Run build
        build_cmd = config.get("build_command", "npm run build")
        log(f"Running build: {build_cmd}")
        process = await asyncio.create_subprocess_shell(
            build_cmd,
            cwd=source_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env={**os.environ, **environment}
        )

        async for line in process.stdout:
            log(line.decode('utf-8', errors='replace').rstrip())

        await process.wait()
        if process.returncode != 0:
            raise Exception("NPM build failed")

        # Determine output directory
        output_dir = config.get("output_dir", "dist")
        artifact_path = os.path.join(source_path, output_dir)

        log(f"Build completed. Artifact: {artifact_path}")
        return {"artifact_path": artifact_path, "type": "npm_build"}

    async def _build_python(self, build_id: str, config: Dict, source_path: str,
                           environment: Dict, log) -> Dict:
        """Build Python project"""
        if not source_path or not os.path.exists(source_path):
            raise Exception("Source path required for Python build")

        log(f"Building Python project: {source_path}")

        # Check for setup.py or pyproject.toml
        has_setup = os.path.exists(os.path.join(source_path, "setup.py"))
        has_pyproject = os.path.exists(os.path.join(source_path, "pyproject.toml"))

        if not has_setup and not has_pyproject:
            raise Exception("No setup.py or pyproject.toml found")

        # Build command
        build_cmd = config.get("build_command", "python -m build")
        log(f"Running build: {build_cmd}")

        process = await asyncio.create_subprocess_shell(
            build_cmd,
            cwd=source_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env={**os.environ, **environment}
        )

        async for line in process.stdout:
            log(line.decode('utf-8', errors='replace').rstrip())

        await process.wait()
        if process.returncode != 0:
            raise Exception("Python build failed")

        # Find artifact
        dist_dir = os.path.join(source_path, "dist")
        if os.path.exists(dist_dir):
            artifacts = os.listdir(dist_dir)
            log(f"Build artifacts: {artifacts}")
            return {"artifact_path": dist_dir, "type": "python_package"}

        return {"artifact_path": source_path, "type": "python_package"}

    async def _build_custom(self, build_id: str, config: Dict, source_path: str,
                           environment: Dict, log) -> Dict:
        """Run custom build script"""
        script = config.get("script")
        if not script:
            raise Exception("Custom build requires script")

        log(f"Running custom build script")

        working_dir = source_path or tempfile.gettempdir()
        process = await asyncio.create_subprocess_shell(
            script,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env={**os.environ, **environment}
        )

        async for line in process.stdout:
            log(line.decode('utf-8', errors='replace').rstrip())

        await process.wait()
        if process.returncode != 0:
            raise Exception(f"Custom build failed with exit code {process.returncode}")

        return {"artifact_path": config.get("artifact_path", working_dir), "type": "custom"}

    async def _update_build(self, build_id: str, status: str, logs: str,
                           artifact_path: str = None, duration: int = None):
        """Update build record"""
        updates = ["status = $2", "logs = $3", "updated_at = NOW()"]
        params = [build_id, status, logs]
        param_idx = 4

        if artifact_path:
            updates.append(f"artifact_path = ${param_idx}")
            params.append(artifact_path)
            param_idx += 1

        if duration is not None:
            updates.append(f"duration_seconds = ${param_idx}")
            params.append(duration)
            param_idx += 1

        if status in ("completed", "failed"):
            updates.append("completed_at = NOW()")

        query = f"UPDATE builds SET {', '.join(updates)} WHERE id = $1"
        await db.execute(query, *params)

    async def _update_build_logs(self, build_id: str, logs: str):
        """Update build logs"""
        await db.execute(
            "UPDATE builds SET logs = $1, updated_at = NOW() WHERE id = $2",
            logs, build_id
        )

    # ==================== Query Methods ====================

    async def get_build(self, build_id: str) -> Optional[Dict]:
        """Get build by ID"""
        row = await db.fetchrow("SELECT * FROM builds WHERE id = $1", build_id)
        return dict(row) if row else None

    async def list_builds(self, project_id: str = None, status: str = None,
                         limit: int = 100, offset: int = 0) -> List[Dict]:
        """List builds"""
        query = "SELECT * FROM builds WHERE 1=1"
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

    async def cancel_build(self, build_id: str) -> bool:
        """Cancel a running build"""
        task = self.running_builds.get(build_id)
        if task:
            task.cancel()
            await self._update_build(build_id, "cancelled", "Build cancelled by user")
            return True
        return False

    async def get_build_logs(self, build_id: str) -> Optional[str]:
        """Get build logs"""
        row = await db.fetchrow("SELECT logs FROM builds WHERE id = $1", build_id)
        return row["logs"] if row else None


builder = Builder()