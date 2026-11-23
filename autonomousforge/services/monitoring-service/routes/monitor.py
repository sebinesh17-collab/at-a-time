"""
Monitoring Service routes
"""
from aiohttp import web
from aiohttp.web import Request, json_response
from typing import Optional
from uuid import UUID
from datetime import datetime

from ..services.monitor import monitor
from ..database import db
from ..models.schemas import (
    MetricCreate, MetricBatchCreate, MetricResponse,
    MetricQuery, MetricQueryResponse,
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse,
    AlertResponse, AlertUpdate,
    ServiceHealthCreate, ServiceHealthResponse,
    DashboardCreate, DashboardResponse,
    MetricFilter, AlertFilter, ServiceHealthFilter, DashboardFilter,
    MonitoringStatsResponse, HealthResponse
)


def require_auth(handler):
    """Decorator to require authentication"""
    async def wrapper(request: Request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return json_response({"error": "unauthorized", "message": "Missing or invalid authorization header"}, status=401)

        token = auth_header[7:]
        if token.startswith("af_master_"):
            request["owner_id"] = "master"
            request["is_master"] = True
            return await handler(request)

        request["owner_id"] = "00000000-0000-0000-0000-000000000001"
        request["is_master"] = False
        return await handler(request)
    return wrapper


# ==================== Metrics ====================

@require_auth
async def record_metric(request: Request):
    """Record a custom metric"""
    try:
        data = await request.json()
        create_request = MetricCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    result = await monitor.record_metric(
        create_request.name, create_request.value,
        create_request.metric_type,
        create_request.labels,
        create_request.timestamp
    )
    return json_response(result, status=201)


@require_auth
async def record_metrics_batch(request: Request):
    """Record multiple metrics at once"""
    try:
        data = await request.json()
        batch_request = MetricBatchCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    results = []
    for metric in batch_request.metrics:
        result = await monitor.record_metric(
            metric.name, metric.value,
            metric.metric_type,
            metric.labels,
            metric.timestamp
        )
        results.append(result)
    return json_response({"metrics": results}, status=201)


@require_auth
async def get_metrics(request: Request):
    """Get metric history"""
    name = request.query.get("name")
    if not name:
        return json_response({"error": "validation_error", "message": "name required"}, status=400)

    since_str = request.query.get("since")
    since = None
    if since_str:
        since = datetime.fromisoformat(since_str.replace('Z', '+00:00'))

    until_str = request.query.get("until")
    until = None
    if until_str:
        until = datetime.fromisoformat(until_str.replace('Z', '+00:00'))

    labels_filter = request.query.get("labels")
    limit = min(int(request.query.get("limit", 1000)), 5000)

    filter_params = MetricFilter(
        name=name,
        labels=labels_filter,
        start_time=since,
        end_time=until,
        limit=limit
    )

    metrics = await monitor.get_metrics(
        filter_params.name,
        filter_params.start_time,
        filter_params.limit
    )
    return json_response(metrics)


@require_auth
async def query_metrics(request: Request):
    """Query metrics with aggregation"""
    try:
        data = await request.json()
        query_request = MetricQuery(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    data_points = await monitor.query_metrics(
        query_request.name,
        query_request.labels,
        query_request.start_time,
        query_request.end_time,
        query_request.step_seconds,
        query_request.aggregation
    )

    response = MetricQueryResponse(
        name=query_request.name,
        labels=query_request.labels or {},
        data_points=data_points,
        aggregation=query_request.aggregation
    )
    return json_response(response.model_dump())


# ==================== Alert Rules ====================

@require_auth
async def create_alert_rule(request: Request):
    """Create an alert rule"""
    try:
        data = await request.json()
        create_request = AlertRuleCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    rule = await monitor.create_alert_rule(create_request.model_dump())
    return json_response(rule, status=201)


@require_auth
async def get_alert_rule(request: Request):
    """Get alert rule by ID"""
    rule_id = request.match_info.get("rule_id")
    try:
        rule_uuid = UUID(rule_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid rule ID"}, status=400)

    rule = await monitor.get_alert_rule(str(rule_uuid))
    if not rule:
        return json_response({"error": "not_found", "message": "Alert rule not found"}, status=404)
    return json_response(rule)


@require_auth
async def update_alert_rule(request: Request):
    """Update alert rule"""
    rule_id = request.match_info.get("rule_id")
    try:
        rule_uuid = UUID(rule_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid rule ID"}, status=400)

    try:
        data = await request.json()
        update_request = AlertRuleUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    rule = await monitor.update_alert_rule(str(rule_uuid), update_request.model_dump(exclude_unset=True))
    if not rule:
        return json_response({"error": "not_found", "message": "Alert rule not found"}, status=404)
    return json_response(rule)


@require_auth
async def delete_alert_rule(request: Request):
    """Delete alert rule"""
    rule_id = request.match_info.get("rule_id")
    try:
        rule_uuid = UUID(rule_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid rule ID"}, status=400)

    success = await monitor.delete_alert_rule(str(rule_uuid))
    if not success:
        return json_response({"error": "not_found", "message": "Alert rule not found"}, status=404)
    return json_response({"message": "Alert rule deleted"})


@require_auth
async def list_alert_rules(request: Request):
    """List alert rules"""
    is_enabled = request.query.get("is_enabled")
    severity = request.query.get("severity")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = AlertFilter(
        is_enabled=is_enabled.lower() == "true" if is_enabled else None,
        severity=severity,
        limit=limit,
        offset=offset
    )

    rules = await monitor.list_alert_rules(
        filter_params.is_enabled,
        filter_params.severity,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(rules)


@require_auth
async def get_active_alerts(request: Request):
    """Get active alerts"""
    severity = request.query.get("severity")
    limit = min(int(request.query.get("limit", 100)), 500)
    offset = int(request.query.get("offset", 0))

    alerts = await monitor.get_active_alerts(
        severity,
        limit,
        offset
    )
    return json_response(alerts)


@require_auth
async def acknowledge_alert(request: Request):
    """Acknowledge an alert"""
    alert_id = request.match_info.get("alert_id")
    try:
        alert_uuid = UUID(alert_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid alert ID"}, status=400)

    try:
        data = await request.json()
        update_request = AlertUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    alert = await monitor.acknowledge_alert(str(alert_uuid), update_request.acknowledged_by)
    if not alert:
        return json_response({"error": "not_found", "message": "Alert not found"}, status=404)
    return json_response(alert)


# ==================== Monitored Services ====================

@require_auth
async def register_service(request: Request):
    """Register a service for monitoring"""
    try:
        data = await request.json()
        create_request = ServiceHealthCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    service = await monitor.register_service(create_request.model_dump())
    return json_response(service, status=201)


@require_auth
async def get_service(request: Request):
    """Get monitored service by ID"""
    service_id = request.match_info.get("service_id")
    try:
        service_uuid = UUID(service_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid service ID"}, status=400)

    service = await monitor.get_service(str(service_uuid))
    if not service:
        return json_response({"error": "not_found", "message": "Service not found"}, status=404)
    return json_response(service)


@require_auth
async def list_services(request: Request):
    """List monitored services"""
    status = request.query.get("status")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = ServiceHealthFilter(
        status=status,
        limit=limit,
        offset=offset
    )

    services = await monitor.list_services(
        filter_params.status,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(services)


@require_auth
async def get_service_health(request: Request):
    """Get health check history for a service"""
    service_id = request.match_info.get("service_id")
    try:
        service_uuid = UUID(service_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid service ID"}, status=400)

    limit = min(int(request.query.get("limit", 100)), 500)

    health = await monitor.get_service_health(str(service_uuid), limit)
    return json_response({"health_checks": health})


# ==================== Dashboards ====================

@require_auth
async def create_dashboard(request: Request):
    """Create a dashboard"""
    try:
        data = await request.json()
        create_request = DashboardCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    dashboard = await monitor.create_dashboard(create_request.model_dump())
    return json_response(dashboard, status=201)


@require_auth
async def get_dashboard(request: Request):
    """Get dashboard by ID"""
    dashboard_id = request.match_info.get("dashboard_id")
    try:
        dashboard_uuid = UUID(dashboard_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid dashboard ID"}, status=400)

    dashboard = await monitor.get_dashboard(str(dashboard_uuid))
    if not dashboard:
        return json_response({"error": "not_found", "message": "Dashboard not found"}, status=404)
    return json_response(dashboard)


@require_auth
async def list_dashboards(request: Request):
    """List dashboards"""
    is_default = request.query.get("is_default")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = DashboardFilter(
        is_default=is_default.lower() == "true" if is_default else None,
        limit=limit,
        offset=offset
    )

    dashboards = await monitor.list_dashboards(
        filter_params.is_default,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(dashboards)


@require_auth
async def get_monitoring_stats(request: Request):
    """Get monitoring statistics"""
    stats = await monitor.get_stats()
    return json_response(stats)


# ==================== Health ====================

async def health_check(request: Request):
    """Health check"""
    try:
        await db.fetchval("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"

    return json_response(HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        service="monitoring-service",
        version="1.0.0",
        database=db_status,
        total_metrics=0,
        active_alerts=0
    ).model_dump())


# Route registration
def setup_routes(app: web.Application):
    app.router.add_get("/health", health_check)

    # Metrics
    app.router.add_post("/api/metrics", record_metric)
    app.router.add_post("/api/metrics/batch", record_metrics_batch)
    app.router.add_get("/api/metrics", get_metrics)
    app.router.add_post("/api/metrics/query", query_metrics)

    # Alert Rules
    app.router.add_post("/api/alerts/rules", create_alert_rule)
    app.router.add_get("/api/alerts/rules", list_alert_rules)
    app.router.add_get("/api/alerts/rules/{rule_id}", get_alert_rule)
    app.router.add_patch("/api/alerts/rules/{rule_id}", update_alert_rule)
    app.router.add_delete("/api/alerts/rules/{rule_id}", delete_alert_rule)
    app.router.add_get("/api/alerts/active", get_active_alerts)
    app.router.add_post("/api/alerts/{alert_id}/acknowledge", acknowledge_alert)

    # Monitored Services
    app.router.add_post("/api/services", register_service)
    app.router.add_get("/api/services", list_services)
    app.router.add_get("/api/services/{service_id}", get_service)
    app.router.add_get("/api/services/{service_id}/health", get_service_health)

    # Dashboards
    app.router.add_post("/api/dashboards", create_dashboard)
    app.router.add_get("/api/dashboards", list_dashboards)
    app.router.add_get("/api/dashboards/{dashboard_id}", get_dashboard)

    # Stats
    app.router.add_get("/api/stats", get_monitoring_stats)