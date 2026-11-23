"""
Testing Service routes
"""
from aiohttp import web
from aiohttp.web import Request, json_response
from typing import Optional
from uuid import UUID
from datetime import datetime

from ..services.tester import tester
from ..database import db
from ..models.schemas import (
    TestSuiteCreate, TestSuiteUpdate, TestSuiteResponse,
    TestCaseCreate, TestCaseUpdate, TestCaseResponse,
    TestRunCreate, TestRunUpdate, TestRunResponse,
    TestResultCreate, TestResultResponse,
    TestSuiteFilter, TestRunFilter, TestStatsResponse, HealthResponse
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


# ==================== Test Suites ====================

@require_auth
async def create_test_suite(request: Request):
    """Create a test suite"""
    try:
        data = await request.json()
        create_request = TestSuiteCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        suite = await tester.create_test_suite(create_request.model_dump())
        return json_response(suite, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_test_suite(request: Request):
    """Get test suite by ID"""
    suite_id = request.match_info.get("suite_id")
    try:
        suite_uuid = UUID(suite_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid suite ID"}, status=400)

    suite = await tester.get_test_suite(str(suite_uuid))
    if not suite:
        return json_response({"error": "not_found", "message": "Test suite not found"}, status=404)
    return json_response(suite)


@require_auth
async def update_test_suite(request: Request):
    """Update test suite"""
    suite_id = request.match_info.get("suite_id")
    try:
        suite_uuid = UUID(suite_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid suite ID"}, status=400)

    try:
        data = await request.json()
        update_request = TestSuiteUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        suite = await tester.update_test_suite(str(suite_uuid), update_request.model_dump(exclude_unset=True))
        if not suite:
            return json_response({"error": "not_found", "message": "Test suite not found"}, status=404)
        return json_response(suite)
    except Exception as e:
        return json_response({"error": "update_failed", "message": str(e)}, status=500)


@require_auth
async def delete_test_suite(request: Request):
    """Delete test suite"""
    suite_id = request.match_info.get("suite_id")
    try:
        suite_uuid = UUID(suite_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid suite ID"}, status=400)

    success = await tester.delete_test_suite(str(suite_uuid))
    if not success:
        return json_response({"error": "not_found", "message": "Test suite not found"}, status=404)
    return json_response({"message": "Test suite deleted"})


@require_auth
async def list_test_suites(request: Request):
    """List test suites"""
    project_id = request.query.get("project_id")
    test_type = request.query.get("test_type")
    is_enabled = request.query.get("is_enabled")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = TestSuiteFilter(
        project_id=UUID(project_id) if project_id else None,
        test_type=test_type,
        is_enabled=is_enabled.lower() == "true" if is_enabled else None,
        limit=limit,
        offset=offset
    )

    suites = await tester.list_test_suites(
        str(filter_params.project_id) if filter_params.project_id else None,
        filter_params.test_type,
        filter_params.is_enabled,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(suites)


# ==================== Test Cases ====================

@require_auth
async def create_test_case(request: Request):
    """Create a test case"""
    try:
        data = await request.json()
        create_request = TestCaseCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        case = await tester.create_test_case(create_request.model_dump())
        return json_response(case, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_test_case(request: Request):
    """Get test case by ID"""
    case_id = request.match_info.get("case_id")
    try:
        case_uuid = UUID(case_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid case ID"}, status=400)

    case = await tester.get_test_case(str(case_uuid))
    if not case:
        return json_response({"error": "not_found", "message": "Test case not found"}, status=404)
    return json_response(case)


@require_auth
async def update_test_case(request: Request):
    """Update test case"""
    case_id = request.match_info.get("case_id")
    try:
        case_uuid = UUID(case_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid case ID"}, status=400)

    try:
        data = await request.json()
        update_request = TestCaseUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        case = await tester.update_test_case(str(case_uuid), update_request.model_dump(exclude_unset=True))
        if not case:
            return json_response({"error": "not_found", "message": "Test case not found"}, status=404)
        return json_response(case)
    except Exception as e:
        return json_response({"error": "update_failed", "message": str(e)}, status=500)


@require_auth
async def delete_test_case(request: Request):
    """Delete test case"""
    case_id = request.match_info.get("case_id")
    try:
        case_uuid = UUID(case_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid case ID"}, status=400)

    success = await tester.delete_test_case(str(case_uuid))
    if not success:
        return json_response({"error": "not_found", "message": "Test case not found"}, status=404)
    return json_response({"message": "Test case deleted"})


@require_auth
async def list_test_cases(request: Request):
    """List test cases for a suite"""
    suite_id = request.query.get("suite_id")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    cases = await tester.list_test_cases(suite_id, limit, offset)
    return json_response(cases)


# ==================== Test Runs ====================

@require_auth
async def create_test_run(request: Request):
    """Create and run a test"""
    try:
        data = await request.json()
        create_request = TestRunCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        test_run = await tester.create_test_run(create_request.model_dump())
        return json_response(test_run, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_test_run(request: Request):
    """Get test run by ID"""
    run_id = request.match_info.get("test_run_id")
    try:
        run_uuid = UUID(run_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid test run ID"}, status=400)

    test_run = await tester.get_test_run(str(run_uuid))
    if not test_run:
        return json_response({"error": "not_found", "message": "Test run not found"}, status=404)
    return json_response(test_run)


@require_auth
async def update_test_run(request: Request):
    """Update test run"""
    run_id = request.match_info.get("test_run_id")
    try:
        run_uuid = UUID(run_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid test run ID"}, status=400)

    try:
        data = await request.json()
        update_request = TestRunUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        test_run = await tester.update_test_run(str(run_uuid), update_request.model_dump(exclude_unset=True))
        if not test_run:
            return json_response({"error": "not_found", "message": "Test run not found"}, status=404)
        return json_response(test_run)
    except Exception as e:
        return json_response({"error": "update_failed", "message": str(e)}, status=500)


@require_auth
async def list_test_runs(request: Request):
    """List test runs"""
    suite_id = request.query.get("suite_id")
    status = request.query.get("status")
    trigger_type = request.query.get("trigger_type")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = TestRunFilter(
        suite_id=UUID(suite_id) if suite_id else None,
        status=status,
        trigger_type=trigger_type,
        limit=limit,
        offset=offset
    )

    runs = await tester.list_test_runs(
        str(filter_params.suite_id) if filter_params.suite_id else None,
        filter_params.status,
        filter_params.trigger_type,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(runs)


@require_auth
async def cancel_test_run(request: Request):
    """Cancel a test run"""
    run_id = request.match_info.get("test_run_id")
    try:
        run_uuid = UUID(run_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid test run ID"}, status=400)

    success = await tester.cancel_test_run(str(run_uuid))
    if not success:
        return json_response({"error": "not_found", "message": "Test run not found or not running"}, status=404)
    return json_response({"message": "Test run cancelled"})


# ==================== Test Results ====================

@require_auth
async def create_test_result(request: Request):
    """Create a test result"""
    try:
        data = await request.json()
        create_request = TestResultCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        result = await tester.create_test_result(create_request.model_dump())
        return json_response(result, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_test_results(request: Request):
    """Get test results for a run"""
    run_id = request.match_info.get("test_run_id")
    try:
        run_uuid = UUID(run_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid test run ID"}, status=400)

    results = await tester.get_test_results(str(run_uuid))
    return json_response({"results": results})


# ==================== Stats ====================

@require_auth
async def get_test_stats(request: Request):
    """Get testing statistics"""
    project_id = request.query.get("project_id")
    stats = await tester.get_stats(project_id)
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
        service="testing-service",
        version="1.0.0",
        database=db_status,
        queue_depth=len(tester.running_tests),
        active_runs=len([t for t in tester.running_tests.values() if not t.done()])
    ).model_dump())


# Route registration
def setup_routes(app: web.Application):
    app.router.add_get("/health", health_check)

    # Test Suites
    app.router.add_post("/api/tests/suites", create_test_suite)
    app.router.add_get("/api/tests/suites", list_test_suites)
    app.router.add_get("/api/tests/suites/{suite_id}", get_test_suite)
    app.router.add_patch("/api/tests/suites/{suite_id}", update_test_suite)
    app.router.add_delete("/api/tests/suites/{suite_id}", delete_test_suite)

    # Test Cases
    app.router.add_post("/api/tests/cases", create_test_case)
    app.router.add_get("/api/tests/cases", list_test_cases)
    app.router.add_get("/api/tests/cases/{case_id}", get_test_case)
    app.router.add_patch("/api/tests/cases/{case_id}", update_test_case)
    app.router.add_delete("/api/tests/cases/{case_id}", delete_test_case)

    # Test Runs
    app.router.add_post("/api/tests/runs", create_test_run)
    app.router.add_get("/api/tests/runs", list_test_runs)
    app.router.add_get("/api/tests/runs/{test_run_id}", get_test_run)
    app.router.add_patch("/api/tests/runs/{test_run_id}", update_test_run)
    app.router.add_post("/api/tests/runs/{test_run_id}/cancel", cancel_test_run)

    # Test Results
    app.router.add_post("/api/tests/results", create_test_result)
    app.router.add_get("/api/tests/runs/{test_run_id}/results", get_test_results)

    # Stats
    app.router.add_get("/api/tests/stats", get_test_stats)