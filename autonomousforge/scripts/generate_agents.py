#!/usr/bin/env python3
"""
AUTONOMOUSFORGE Agent Hierarchy Generator
Generates 16,111 logical agents: 1 Master + 10 Principals + 100 Heads + 1000 Team Leaders + 15000 Workers
"""

import asyncio
import asyncpg
import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from packages.shared_types.enums import AgentLevel, AgentStatus


# Department assignments for Principals
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


def generate_master_agent() -> Dict[str, Any]:
    """Generate the Master Orchestrator (M-001)"""
    return {
        "agent_id": "M-001",
        "name": "Master Orchestrator",
        "level": AgentLevel.MASTER.value,
        "parent_id": None,
        "department": "Executive",
        "domain": "Full System",
        "status": AgentStatus.ACTIVE.value,
        "capabilities": json.dumps([
            "strategic_planning", "resource_allocation", "system_monitoring",
            "decision_authority", "master_key_holder", "cross_department_coordination"
        ]),
        "configuration": json.dumps({
            "reports_to": "BOSS",
            "master_api_key_access": True,
            "full_database_access": True,
            "can_communicate_with_any_agent": True
        }),
        "metadata": json.dumps({
            "created_at": datetime.utcnow().isoformat(),
            "hierarchy_level": 0,
            "total_subordinates": 16110
        })
    }


def generate_principals() -> List[Dict[str, Any]]:
    """Generate 10 Principal agents (P-01 through P-10)"""
    principals = []
    for i in range(1, 11):
        agent_id = f"P-{i:02d}"
        principals.append({
            "agent_id": agent_id,
            "name": f"Principal {agent_id} - {PRINCIPAL_DEPARTMENTS[agent_id]}",
            "level": AgentLevel.PRINCIPAL.value,
            "parent_id": "M-001",
            "department": PRINCIPAL_DEPARTMENTS[agent_id],
            "domain": PRINCIPAL_DEPARTMENTS[agent_id],
            "status": AgentStatus.ACTIVE.value,
            "capabilities": json.dumps([
                "domain_strategy", "resource_management", "cross_team_coordination",
                "quality_standards", "status_reporting", "epic_decomposition"
            ]),
            "configuration": json.dumps({
                "reports_to": "M-001",
                "manages_heads": 10,
                "head_range": f"H-{(i-1)*10 + 1:03d} to H-{i*10:03d}",
                "department_index": i
            }),
            "metadata": json.dumps({
                "created_at": datetime.utcnow().isoformat(),
                "hierarchy_level": 1,
                "total_subordinates": 1610  # 10 heads * (10 TLs * 15 workers + 10 TLs + 1 head)
            })
        })
    return principals


def generate_heads() -> List[Dict[str, Any]]:
    """Generate 100 Head agents (H-001 through H-100)"""
    heads = []
    for principal_idx in range(1, 11):
        principal_id = f"P-{principal_idx:02d}"
        domains = HEAD_DOMAINS[principal_id]
        for head_idx in range(1, 11):
            head_number = (principal_idx - 1) * 10 + head_idx
            agent_id = f"H-{head_number:03d}"
            heads.append({
                "agent_id": agent_id,
                "name": f"Head {agent_id} - {domains[head_idx - 1]}",
                "level": AgentLevel.HEAD.value,
                "parent_id": principal_id,
                "department": PRINCIPAL_DEPARTMENTS[principal_id],
                "domain": domains[head_idx - 1],
                "status": AgentStatus.ACTIVE.value,
                "capabilities": json.dumps([
                    "sprint_planning", "technical_leadership", "resource_allocation",
                    "code_review", "blocker_resolution", "status_aggregation",
                    "feature_decomposition"
                ]),
                "configuration": json.dumps({
                    "reports_to": principal_id,
                    "manages_team_leaders": 10,
                    "tl_range": f"TL-{(head_number-1)*10 + 1:03d} to TL-{head_number*10:03d}",
                    "head_index": head_number
                }),
                "metadata": json.dumps({
                    "created_at": datetime.utcnow().isoformat(),
                    "hierarchy_level": 2,
                    "total_subordinates": 160  # 10 TLs * 15 workers + 10 TLs
                })
            })
    return heads


def generate_team_leaders() -> List[Dict[str, Any]]:
    """Generate 1000 Team Leader agents (TL-001 through TL-1000)"""
    team_leaders = []
    for head_idx in range(1, 101):
        head_id = f"H-{head_idx:03d}"
        for tl_idx in range(1, 11):
            tl_number = (head_idx - 1) * 10 + tl_idx
            agent_id = f"TL-{tl_number:03d}"
            team_leaders.append({
                "agent_id": agent_id,
                "name": f"Team Leader {agent_id}",
                "level": AgentLevel.TEAM_LEADER.value,
                "parent_id": head_id,
                "department": "",  # Will be filled from head
                "domain": "",  # Will be filled from head
                "status": AgentStatus.ACTIVE.value,
                "capabilities": json.dumps([
                    "task_decomposition", "direct_implementation", "sprint_execution",
                    "code_review", "mentorship", "status_reporting",
                    "microtask_assignment"
                ]),
                "configuration": json.dumps({
                    "reports_to": head_id,
                    "manages_workers": 15,
                    "worker_range": f"W-{(tl_number-1)*15 + 1:05d} to W-{tl_number*15:05d}",
                    "tl_index": tl_number,
                    "work_distribution": {
                        "direct_execution": 0.40,
                        "code_review": 0.30,
                        "planning_coordination": 0.20,
                        "mentorship_process": 0.10
                    }
                }),
                "metadata": json.dumps({
                    "created_at": datetime.utcnow().isoformat(),
                    "hierarchy_level": 3,
                    "total_subordinates": 15
                })
            })
    return team_leaders


def generate_workers() -> List[Dict[str, Any]]:
    """Generate 15000 Worker agents (W-00001 through W-15000)"""
    workers = []
    for tl_idx in range(1, 1001):
        tl_id = f"TL-{tl_idx:03d}"
        for worker_idx in range(1, 16):
            worker_number = (tl_idx - 1) * 15 + worker_idx
            agent_id = f"W-{worker_number:05d}"
            # Assign 2-3 random skills
            import random
            num_skills = random.randint(2, 3)
            skills = random.sample(WORKER_SKILLS, num_skills)

            workers.append({
                "agent_id": agent_id,
                "name": f"Worker {agent_id}",
                "level": AgentLevel.WORKER.value,
                "parent_id": tl_id,
                "department": "",  # Will be filled from TL -> Head
                "domain": "",  # Will be filled from TL -> Head
                "status": AgentStatus.ACTIVE.value,
                "capabilities": json.dumps([
                    "atomic_task_execution", "code_implementation", "testing",
                    "documentation", "self_review", "progress_reporting"
                ]),
                "configuration": json.dumps({
                    "reports_to": tl_id,
                    "skills": skills,
                    "worker_index": worker_number,
                    "task_levels": ["microtask", "atomic"],
                    "max_concurrent_tasks": 2
                }),
                "metadata": json.dumps({
                    "created_at": datetime.utcnow().isoformat(),
                    "hierarchy_level": 4,
                    "total_subordinates": 0
                })
            })
    return workers


async def insert_agents(pool: asyncpg.Pool, agents: List[Dict[str, Any]], batch_size: int = 500):
    """Insert agents in batches"""
    total = len(agents)
    print(f"Inserting {total} agents in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch = agents[i:i + batch_size]
        async with pool.acquire() as conn:
            async with conn.transaction():
                for agent in batch:
                    await conn.execute("""
                        INSERT INTO agents (
                            agent_id, name, level, parent_id, department, domain,
                            status, capabilities, configuration, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (agent_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            level = EXCLUDED.level,
                            parent_id = EXCLUDED.parent_id,
                            department = EXCLUDED.department,
                            domain = EXCLUDED.domain,
                            status = EXCLUDED.status,
                            capabilities = EXCLUDED.capabilities,
                            configuration = EXCLUDED.configuration,
                            metadata = EXCLUDED.metadata
                    """,
                        agent["agent_id"],
                        agent["name"],
                        agent["level"],
                        agent["parent_id"],
                        agent["department"],
                        agent["domain"],
                        agent["status"],
                        agent["capabilities"],
                        agent["configuration"],
                        agent["metadata"]
                    )
        print(f"  Inserted {min(i + batch_size, total)}/{total} agents")


async def update_department_domain(pool: asyncpg.Pool):
    """Update department and domain for Team Leaders and Workers from their parents"""
    print("Updating department/domain for Team Leaders and Workers...")

    async with pool.acquire() as conn:
        # Update Team Leaders from Heads
        await conn.execute("""
            UPDATE agents tl
            SET department = h.department, domain = h.domain
            FROM agents h
            WHERE tl.parent_id = h.agent_id
            AND tl.level = 'team_leader'
            AND h.level = 'head'
        """)

        # Update Workers from Team Leaders -> Heads
        await conn.execute("""
            UPDATE agents w
            SET department = h.department, domain = h.domain
            FROM agents tl
            JOIN agents h ON tl.parent_id = h.agent_id
            WHERE w.parent_id = tl.agent_id
            AND w.level = 'worker'
            AND tl.level = 'team_leader'
            AND h.level = 'head'
        """)

    print("Department/domain update complete")


async def verify_hierarchy(pool: asyncpg.Pool):
    """Verify the agent hierarchy is correct"""
    print("\nVerifying hierarchy...")

    async with pool.acquire() as conn:
        # Count by level
        counts = await conn.fetch("""
            SELECT level, COUNT(*) as count
            FROM agents
            GROUP BY level
            ORDER BY
                CASE level
                    WHEN 'master' THEN 1
                    WHEN 'principal' THEN 2
                    WHEN 'head' THEN 3
                    WHEN 'team_leader' THEN 4
                    WHEN 'worker' THEN 5
                END
        """)

        print("\nAgent counts by level:")
        total = 0
        for row in counts:
            print(f"  {row['level']:15s}: {row['count']:6d}")
            total += row['count']
        print(f"  {'TOTAL':15s}: {total:6d}")

        # Verify parent-child relationships
        print("\nVerifying parent-child relationships...")

        # Master has no parent
        master_parent = await conn.fetchval("SELECT parent_id FROM agents WHERE agent_id = 'M-001'")
        print(f"  M-001 parent: {master_parent} (should be None)")

        # Principals report to Master
        principal_parents = await conn.fetch("""
            SELECT agent_id, parent_id FROM agents
            WHERE level = 'principal' ORDER BY agent_id
        """)
        for p in principal_parents:
            print(f"  {p['agent_id']} -> {p['parent_id']}")

        # Sample Heads
        head_parents = await conn.fetch("""
            SELECT agent_id, parent_id FROM agents
            WHERE level = 'head' ORDER BY agent_id LIMIT 5
        """)
        for h in head_parents:
            print(f"  {h['agent_id']} -> {h['parent_id']}")

        # Sample Team Leaders
        tl_parents = await conn.fetch("""
            SELECT agent_id, parent_id FROM agents
            WHERE level = 'team_leader' ORDER BY agent_id LIMIT 5
        """)
        for tl in tl_parents:
            print(f"  {tl['agent_id']} -> {tl['parent_id']}")

        # Sample Workers
        worker_parents = await conn.fetch("""
            SELECT agent_id, parent_id FROM agents
            WHERE level = 'worker' ORDER BY agent_id LIMIT 5
        """)
        for w in worker_parents:
            print(f"  {w['agent_id']} -> {w['parent_id']}")

        # Total count verification
        expected = 1 + 10 + 100 + 1000 + 15000
        print(f"\nExpected total: {expected}")
        print(f"Actual total:   {total}")
        print(f"Match: {'YES' if total == expected else 'NO'}")


async def main():
    """Main generation function"""
    database_url = os.getenv("DATABASE_URL", "postgresql://forge:forge_secure_password@localhost:5432/autonomousforge")

    print("=" * 60)
    print("AUTONOMOUSFORGE Agent Hierarchy Generator")
    print("=" * 60)
    print(f"Database: {database_url}")
    print()

    # Create connection pool
    pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10)

    try:
        # Generate all agents
        print("Generating agent hierarchy...")

        master = [generate_master_agent()]
        print(f"  Generated 1 Master agent")

        principals = generate_principals()
        print(f"  Generated {len(principals)} Principal agents")

        heads = generate_heads()
        print(f"  Generated {len(heads)} Head agents")

        team_leaders = generate_team_leaders()
        print(f"  Generated {len(team_leaders)} Team Leader agents")

        workers = generate_workers()
        print(f"  Generated {len(workers)} Worker agents")

        all_agents = master + principals + heads + team_leaders + workers
        print(f"\nTotal agents to insert: {len(all_agents)}")

        # Insert all agents
        await insert_agents(pool, all_agents)

        # Update department/domain for TLs and Workers
        await update_department_domain(pool)

        # Verify
        await verify_hierarchy(pool)

        print("\n" + "=" * 60)
        print("Agent hierarchy generation COMPLETE")
        print("=" * 60)

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())