"""
Monitoring Service - Metrics, alerting, and health monitoring
"""
import asyncio
import logging
import json
import psutil
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4

from ..database import db
from ..config import settings

logger = logging.getLogger(__name__)


class Monitor:
    def __init__(self):
        self._running = False
        self._metrics_task: Optional[asyncio.Task] = None
        self._alerts_task: Optional[asyncio.Task] = None
        self._health_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize monitoring"""
        self._running = True
        self._metrics_task = asyncio.create_task(self._collect_metrics_loop())
        self._alerts_task = asyncio.create_task(self._check_alerts_loop())
        self._health_task = asyncio.create_task(self._health_check_loop())
        logger.info("Monitoring service initialized")

    async def shutdown(self):
        """Shutdown monitoring"""
        self._running = False
        for task in [self._metrics_task, self._alerts_task, self._health_task]:
            if task:
                task.cancel()
        await asyncio.gather(
            *[t for t in [self._metrics_task, self._alerts_task, self._health_task] if t],
            return_exceptions=True
        )
        logger.info("Monitoring service shut down")

    # ==================== Metrics Collection ====================

    async def _collect_metrics_loop(self):
        """Collect system metrics periodically"""
        while self._running:
            try:
                await self._collect_system_metrics()
                await self._collect_service_metrics()
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
            await asyncio.sleep(60)  # Collect every minute

    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        now = datetime.utcnow()

        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        await self._record_metric("system.cpu.percent", cpu_percent, "gauge", "%", now)

        # Memory
        memory = psutil.virtual_memory()
        await self._record_metric("system.memory.percent", memory.percent, "gauge", "%", now)
        await self._record_metric("system.memory.used_bytes", memory.used, "gauge", "bytes", now)
        await self._record_metric("system.memory.available_bytes", memory.available, "gauge", "bytes", now)

        # Disk
        disk = psutil.disk_usage('/')
        await self._record_metric("system.disk.percent", disk.percent, "gauge", "%", now)
        await self._record_metric("system.disk.used_bytes", disk.used, "gauge", "bytes", now)
        await self._record_metric("system.disk.free_bytes", disk.free, "gauge", "bytes", now)

        # Network
        net = psutil.net_io_counters()
        await self._record_metric("system.network.bytes_sent", net.bytes_sent, "counter", "bytes", now)
        await self._record_metric("system.network.bytes_recv", net.bytes_recv, "counter", "bytes", now)

        # Process count
        await self._record_metric("system.processes.count", len(psutil.pids()), "gauge", "count", now)

    async def _collect_service_metrics(self):
        """Collect service-level metrics"""
        now = datetime.utcnow()

        # Check each service health
        services = [
            ("auth-service", 8001),
            ("agent-registry", 8003),
            ("task-scheduler", 8004),
            ("model-gateway", 8005),
            ("provider-service", 8006),
            ("file-service", 8007),
            ("memory-service", 8008),
            ("knowledge-service", 8009),
            ("execution-service", 8010),
            ("build-service", 8011),
            ("testing-service", 8012),
            ("monitoring-service", 8013),
        ]

        for service_name, port in services:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://localhost:{port}/health", timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            await self._record_metric(f"service.{service_name}.healthy", 1, "gauge", "bool", now)
                            await self._record_metric(f"service.{service_name}.response_time_ms", 0, "gauge", "ms", now)
                        else:
                            await self._record_metric(f"service.{service_name}.healthy", 0, "gauge", "bool", now)
            except:
                await self._record_metric(f"service.{service_name}.healthy", 0, "gauge", "bool", now)

    async def _record_metric(self, name: str, value: float, metric_type: str,
                            unit: str, timestamp: datetime, tags: Dict = None):
        """Record a metric"""
        await db.execute("""
            INSERT INTO metrics (id, name, value, metric_type, unit, tags, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, str(uuid4()), name, value, metric_type, unit, json.dumps(tags or {}), timestamp)

    # ==================== Alerting ====================

    async def _check_alerts_loop(self):
        """Check alerts periodically"""
        while self._running:
            try:
                await self._evaluate_alerts()
            except Exception as e:
                logger.error(f"Error checking alerts: {e}")
            await asyncio.sleep(settings.alert_check_interval_seconds)

    async def _evaluate_alerts(self):
        """Evaluate alert rules"""
        # Get active alert rules
        rules = await db.fetch("SELECT * FROM alert_rules WHERE is_active = true")

        for rule in rules:
            try:
                await self._evaluate_rule(rule)
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule['id']}: {e}")

    async def _evaluate_rule(self, rule: Dict):
        """Evaluate a single alert rule"""
        metric_name = rule["metric_name"]
        condition = rule["condition"]  # e.g., ">", "<", ">=", "<=", "==", "!="
        threshold = rule["threshold"]
        duration_seconds = rule.get("duration_seconds", 0)

        # Get recent metric values
        since = datetime.utcnow() - timedelta(seconds=max(duration_seconds, 60))
        rows = await db.fetch("""
            SELECT value, timestamp FROM metrics
            WHERE name = $1 AND timestamp >= $2
            ORDER BY timestamp DESC
        """, metric_name, since)

        if not rows:
            return

        # Check condition
        triggered = False
        for row in rows:
            value = row["value"]
            if self._check_condition(value, condition, threshold):
                triggered = True
                break

        if triggered:
            await self._fire_alert(rule, rows[0]["value"])
        else:
            await self._resolve_alert(rule)

    def _check_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Check if condition is met"""
        if condition == ">":
            return value > threshold
        elif condition == "<":
            return value < threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return value == threshold
        elif condition == "!=":
            return value != threshold
        return False

    async def _fire_alert(self, rule: Dict, current_value: float):
        """Fire an alert"""
        # Check if alert already active
        existing = await db.fetchrow("""
            SELECT id FROM alerts WHERE rule_id = $1 AND status = 'firing'
        """, rule["id"])

        if existing:
            return  # Already firing

        alert_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO alerts (id, rule_id, name, severity, message, current_value,
                               threshold, status, fired_at, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, alert_id, rule["id"], rule["name"], rule["severity"],
            rule["message"].format(value=current_value, threshold=rule["threshold"]),
            current_value, rule["threshold"], "firing", now, now)

        logger.warning(f"Alert fired: {rule['name']} - {current_value} {rule['condition']} {rule['threshold']}")

    async def _resolve_alert(self, rule: Dict):
        """Resolve an alert"""
        result = await db.execute("""
            UPDATE alerts SET status = 'resolved', resolved_at = NOW()
            WHERE rule_id = $1 AND status = 'firing'
        """, rule["id"])

        if result != "UPDATE 0":
            logger.info(f"Alert resolved: {rule['name']}")

    # ==================== Health Checks ====================

    async def _health_check_loop(self):
        """Run health checks periodically"""
        while self._running:
            try:
                await self._run_health_checks()
            except Exception as e:
                logger.error(f"Error running health checks: {e}")
            await asyncio.sleep(settings.health_check_interval_seconds)

    async def _run_health_checks(self):
        """Run health checks for all registered services"""
        services = await db.fetch("SELECT * FROM monitored_services WHERE is_active = true")

        for service in services:
            try:
                await self._check_service_health(service)
            except Exception as e:
                logger.error(f"Error checking health for {service['name']}: {e}")

    async def _check_service_health(self, service: Dict):
        """Check health of a single service"""
        check_type = service.get("check_type", "http")
        check_config = service.get("check_config", {})

        healthy = False
        details = {}

        if check_type == "http":
            healthy, details = await self._http_health_check(check_config)
        elif check_type == "tcp":
            healthy, details = await self._tcp_health_check(check_config)
        elif check_type == "database":
            healthy, details = await self._database_health_check(check_config)

        # Record health check result
        check_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO health_checks (id, service_id, healthy, details, checked_at)
            VALUES ($1, $2, $3, $4, $5)
        """, check_id, service["id"], healthy, json.dumps(details), now)

        # Update service status
        status = "healthy" if healthy else "unhealthy"
        await db.execute("""
            UPDATE monitored_services SET status = $1, last_check = $2, updated_at = NOW()
            WHERE id = $3
        """, status, now, service["id"])

    async def _http_health_check(self, config: Dict) -> tuple:
        """HTTP health check"""
        url = config.get("url")
        expected_status = config.get("expected_status", 200)
        timeout = config.get("timeout", 5)

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as resp:
                    healthy = resp.status == expected_status
                    details = {"status": resp.status, "url": url}
                    return healthy, details
        except Exception as e:
            return False, {"error": str(e), "url": url}

    async def _tcp_health_check(self, config: Dict) -> tuple:
        """TCP health check"""
        host = config.get("host")
        port = config.get("port")
        timeout = config.get("timeout", 5)

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True, {"host": host, "port": port}
        except Exception as e:
            return False, {"error": str(e), "host": host, "port": port}

    async def _database_health_check(self, config: Dict) -> tuple:
        """Database health check"""
        try:
            await db.fetchval("SELECT 1")
            return True, {"database": "connected"}
        except Exception as e:
            return False, {"error": str(e)}

    # ==================== Public API ====================

    async def record_metric(self, name: str, value: float, metric_type: str = "gauge",
                           unit: str = "", tags: Dict = None) -> Dict:
        """Record a custom metric"""
        timestamp = datetime.utcnow()
        await self._record_metric(name, value, metric_type, unit, timestamp, tags)
        return {"name": name, "value": value, "timestamp": timestamp.isoformat()}

    async def get_metrics(self, name: str, since: datetime = None,
                         limit: int = 1000) -> List[Dict]:
        """Get metric history"""
        if since is None:
            since = datetime.utcnow() - timedelta(hours=1)

        rows = await db.fetch("""
            SELECT * FROM metrics WHERE name = $1 AND timestamp >= $2
            ORDER BY timestamp DESC LIMIT $3
        """, name, since, limit)
        return [dict(row) for row in rows]

    async def create_alert_rule(self, rule_data: Dict) -> Dict:
        """Create an alert rule"""
        rule_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO alert_rules (id, name, metric_name, condition, threshold,
                                    severity, message, duration_seconds, is_active,
                                    created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """, rule_id, rule_data["name"], rule_data["metric_name"],
            rule_data["condition"], rule_data["threshold"],
            rule_data.get("severity", "warning"), rule_data.get("message", ""),
            rule_data.get("duration_seconds", 0), rule_data.get("is_active", True),
            now, now)

        return await self.get_alert_rule(rule_id)

    async def get_alert_rule(self, rule_id: str) -> Optional[Dict]:
        """Get alert rule by ID"""
        row = await db.fetchrow("SELECT * FROM alert_rules WHERE id = $1", rule_id)
        return dict(row) if row else None

    async def list_alert_rules(self) -> List[Dict]:
        """List alert rules"""
        rows = await db.fetch("SELECT * FROM alert_rules ORDER BY created_at DESC")
        return [dict(row) for row in rows]

    async def get_active_alerts(self) -> List[Dict]:
        """Get active alerts"""
        rows = await db.fetch("""
            SELECT a.*, ar.name as rule_name, ar.metric_name
            FROM alerts a
            JOIN alert_rules ar ON ar.id = a.rule_id
            WHERE a.status = 'firing'
            ORDER BY a.fired_at DESC
        """)
        return [dict(row) for row in rows]

    async def register_service(self, service_data: Dict) -> Dict:
        """Register a service for monitoring"""
        service_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO monitored_services (id, name, check_type, check_config,
                                           is_active, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, service_id, service_data["name"], service_data.get("check_type", "http"),
            json.dumps(service_data.get("check_config", {})),
            service_data.get("is_active", True), "unknown", now, now)

        return await self.get_service(service_id)

    async def get_service(self, service_id: str) -> Optional[Dict]:
        """Get monitored service by ID"""
        row = await db.fetchrow("SELECT * FROM monitored_services WHERE id = $1", service_id)
        return dict(row) if row else None

    async def list_services(self) -> List[Dict]:
        """List monitored services"""
        rows = await db.fetch("SELECT * FROM monitored_services ORDER BY name")
        return [dict(row) for row in rows]

    async def get_service_health(self, service_id: str) -> List[Dict]:
        """Get health check history for a service"""
        rows = await db.fetch("""
            SELECT * FROM health_checks WHERE service_id = $1
            ORDER BY checked_at DESC LIMIT 100
        """, service_id)
        return [dict(row) for row in rows]


monitor = Monitor()