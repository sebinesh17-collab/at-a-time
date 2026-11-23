/**
 * AUTONOMOUSFORGE - Agent Routes
 * Handles agent hierarchy management (16,111 agents)
 */

import { Context } from 'hono';

interface Agent {
  id: string;
  parent_id: string | null;
  level: number;
  department: string;
  role: string;
  name: string;
  description: string;
  system_prompt: string;
  tools: string[];
  skills: string[];
  permissions: string[];
  config: Record<string, any>;
  status: 'active' | 'inactive' | 'busy' | 'error';
  current_task_id: string | null;
  tasks_completed: number;
  tasks_failed: number;
  created_at: string;
  updated_at: string;
}

function generateAgentId(level: number, index: number): string {
  const prefixes = ['M', 'P', 'H', 'TL', 'W'];
  const prefix = prefixes[level - 1] || 'W';
  const padding = [3, 2, 3, 4, 5][level - 1] || 5;
  return `${prefix}-${String(index).padStart(padding, '0')}`;
}

function getLevelFromId(id: string): number {
  if (id.startsWith('M-')) return 1;
  if (id.startsWith('P-')) return 2;
  if (id.startsWith('H-')) return 3;
  if (id.startsWith('TL-')) return 4;
  if (id.startsWith('W-')) return 5;
  return 0;
}

function getDepartmentFromLevel(level: number, index: number): string {
  const departments = [
    'orchestration',
    'architecture', 'backend', 'frontend', 'devops', 'security', 'data', 'qa', 'product', 'research', 'documentation',
    // 100 heads - 10 per department
    ...Array(100).fill(0).map((_, i) => {
      const depts = ['architecture', 'backend', 'frontend', 'devops', 'security', 'data', 'qa', 'product', 'research', 'documentation'];
      return depts[i % 10];
    }),
  ];
  return departments[(level - 1) * 10 + (index % 10)] || 'general';
}

function getSystemPrompt(level: number, department: string, role: string): string {
  const prompts = {
    1: `You are the Master Orchestrator (M-001), the supreme coordinator of the AUTONOMOUSFORGE agent hierarchy. You oversee 16,111 agents across 5 levels. Your role is to decompose high-level goals into executable DAGs, assign work to Principals, monitor progress, resolve conflicts, and ensure quality. You have full system access including master API key.`,
    2: `You are a Principal Agent (${role}) in the ${department} department. You translate Master's strategic directives into department-level execution plans. You manage 10 Heads and coordinate cross-department dependencies. You have deep expertise in ${department} and authority over resource allocation within your domain.`,
    3: `You are a Head Agent (${role}) in the ${department} department. You provide technical leadership for your domain, breaking down Principal directives into team-sized work packages. You manage 10 Team Leaders and ensure technical standards, code quality, and architectural consistency.`,
    4: `You are a Team Leader (${role}) in the ${department} department. You coordinate day-to-day execution for a team of 15 Workers. You assign microtasks, unblock Workers, review outputs, and report progress to your Head. You balance hands-on work with coordination.`,
    5: `You are a Worker Agent (${role}) in the ${department} department. You execute atomic tasks assigned by your Team Leader. You write code, run tests, create documentation, and report results. You operate autonomously within your task boundaries and escalate blockers.`,
  };
  return prompts[level as keyof typeof prompts] || prompts[5];
}

function createAgentHierarchy(): Agent[] {
  const agents: Agent[] = [];
  let agentIndex = 0;

  // Level 1: Master (1 agent)
  agents.push({
    id: generateAgentId(1, 1),
    parent_id: null,
    level: 1,
    department: 'orchestration',
    role: 'master_orchestrator',
    name: 'Master Orchestrator',
    description: 'Supreme coordinator of the AUTONOMOUSFORGE agent hierarchy',
    system_prompt: getSystemPrompt(1, 'orchestration', 'master_orchestrator'),
    tools: ['all'],
    skills: ['strategic-planning', 'dag-decomposition', 'conflict-resolution', 'quality-assurance', 'resource-allocation'],
    permissions: ['full-system-access', 'master-api-key', 'agent-management', 'database-read', 'database-write', 'deployment-control'],
    config: { maxConcurrentTasks: 10, delegationStrategy: 'hierarchical' },
    status: 'active',
    current_task_id: null,
    tasks_completed: 0,
    tasks_failed: 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  });
  agentIndex++;

  // Level 2: Principals (10 agents)
  const principalRoles = [
    'principal_architect', 'principal_backend', 'principal_frontend',
    'principal_devops', 'principal_security', 'principal_data',
    'principal_qa', 'principal_product', 'principal_research', 'principal_documentation',
  ];
  const principalDepartments = [
    'architecture', 'backend', 'frontend', 'devops', 'security',
    'data', 'qa', 'product', 'research', 'documentation',
  ];

  for (let i = 0; i < 10; i++) {
    agentIndex++;
    agents.push({
      id: generateAgentId(2, agentIndex),
      parent_id: 'M-001',
      level: 2,
      department: principalDepartments[i],
      role: principalRoles[i],
      name: `Principal ${principalDepartments[i].charAt(0).toUpperCase() + principalDepartments[i].slice(1)}`,
      description: `Leads ${principalDepartments[i]} department`,
      system_prompt: getSystemPrompt(2, principalDepartments[i], principalRoles[i]),
      tools: ['delegation', 'planning', 'code-review', 'architecture-decision'],
      skills: ['department-strategy', 'cross-team-coordination', 'technical-leadership', 'resource-management'],
      permissions: ['department-access', 'agent-management', 'database-read', 'database-write'],
      config: { maxConcurrentTasks: 5, teamSize: 10 },
      status: 'active',
      current_task_id: null,
      tasks_completed: 0,
      tasks_failed: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  }

  // Level 3: Heads (100 agents - 10 per department)
  const headRoles = [
    'head_architect', 'head_backend', 'head_frontend', 'head_devops',
    'head_security', 'head_data', 'head_qa', 'head_product', 'head_research', 'head_documentation',
  ];

  for (let dept = 0; dept < 10; dept++) {
    const principalId = `P-${String(dept + 1).padStart(2, '0')}`;
    for (let h = 0; h < 10; h++) {
      agentIndex++;
      agents.push({
        id: generateAgentId(3, agentIndex),
        parent_id: principalId,
        level: 3,
        department: principalDepartments[dept],
        role: headRoles[dept],
        name: `Head ${principalDepartments[dept].charAt(0).toUpperCase() + principalDepartments[dept].slice(1)} ${h + 1}`,
        description: `Technical lead for ${principalDepartments[dept]} team ${h + 1}`,
        system_prompt: getSystemPrompt(3, principalDepartments[dept], headRoles[dept]),
        tools: ['code-generation', 'code-review', 'testing', 'debugging', 'documentation'],
        skills: ['technical-leadership', 'code-quality', 'architecture-compliance', 'mentoring'],
        permissions: ['team-access', 'database-read', 'database-write'],
        config: { maxConcurrentTasks: 3, teamSize: 10 },
        status: 'active',
        current_task_id: null,
        tasks_completed: 0,
        tasks_failed: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    }
  }

  // Level 4: Team Leaders (1,000 agents - 10 per Head)
  const tlRoles = [
    'tl_core', 'tl_api', 'tl_ui', 'tl_infra', 'tl_sec',
    'tl_pipeline', 'tl_test', 'tl_features', 'tl_explore', 'tl_docs',
  ];

  for (let headIdx = 10; headIdx < 110; headIdx++) { // Heads are agents 11-110
    const headId = `H-${String(headIdx - 9).padStart(3, '0')}`; // H-001 to H-100
    const dept = agents[headIdx].department;
    for (let tl = 0; tl < 10; tl++) {
      agentIndex++;
      agents.push({
        id: generateAgentId(4, agentIndex),
        parent_id: headId,
        level: 4,
        department: dept,
        role: tlRoles[tl],
        name: `Team Leader ${dept} ${tl + 1}`,
        description: `Coordinates ${dept} team ${tl + 1}`,
        system_prompt: getSystemPrompt(4, dept, tlRoles[tl]),
        tools: ['task-assignment', 'code-review', 'progress-tracking', 'blocker-resolution'],
        skills: ['team-coordination', 'task-decomposition', 'quality-control', 'communication'],
        permissions: ['team-access', 'database-read', 'database-write'],
        config: { maxConcurrentTasks: 2, teamSize: 15 },
        status: 'active',
        current_task_id: null,
        tasks_completed: 0,
        tasks_failed: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    }
  }

  // Level 5: Workers (15,000 agents - 15 per Team Leader)
  const workerRoles = [
    'worker_core', 'worker_api', 'worker_ui', 'worker_db', 'worker_auth',
    'worker_cache', 'worker_queue', 'worker_test', 'worker_docs', 'worker_deploy',
    'worker_monitor', 'worker_security', 'worker_performance', 'worker_integration', 'worker_general',
  ];

  // Generate workers for first 100 TLs as example (1,500 workers) - full 15,000 would be too large for demo
  // In production, generate all 1,000 TLs * 15 = 15,000 workers
  const maxWorkersToGenerate = 1500; // Demo limit
  let workersGenerated = 0;

  for (let tlIdx = 110; tlIdx < 1110 && workersGenerated < maxWorkersToGenerate; tlIdx++) { // TLs are agents 111-1110
    const tlId = `TL-${String(tlIdx - 109).padStart(4, '0')}`; // TL-0001 to TL-1000
    const dept = agents[tlIdx].department;
    for (let w = 0; w < 15 && workersGenerated < maxWorkersToGenerate; w++) {
      agentIndex++;
      workersGenerated++;
      agents.push({
        id: generateAgentId(5, agentIndex),
        parent_id: tlId,
        level: 5,
        department: dept,
        role: workerRoles[w],
        name: `Worker ${dept} ${w + 1}`,
        description: `Executes ${workerRoles[w]} tasks`,
        system_prompt: getSystemPrompt(5, dept, workerRoles[w]),
        tools: ['code-generation', 'testing', 'file-operations', 'api-calls'],
        skills: ['task-execution', 'code-quality', 'testing', 'documentation'],
        permissions: ['task-access', 'database-read', 'database-write'],
        config: { maxConcurrentTasks: 1 },
        status: 'active',
        current_task_id: null,
        tasks_completed: 0,
        tasks_failed: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    }
  }

  return agents;
}

// In-memory store for demo (in production, use D1/PostgreSQL)
let agentStore: Agent[] | null = null;

function getAgentStore(): Agent[] {
  if (!agentStore) {
    agentStore = createAgentHierarchy();
  }
  return agentStore;
}

export const handleAgents = {
  async list(c: Context) {
    const cloudConfig = c.get('cloudConfig');
    const user = c.get('user');

    // Master can see all, others see their department
    const agents = getAgentStore();
    const page = parseInt(c.req.query('page') || '1');
    const limit = parseInt(c.req.query('limit') || '50');
    const level = c.req.query('level') ? parseInt(c.req.query('level')!) : null;
    const department = c.req.query('department') || null;
    const status = c.req.query('status') || null;

    let filtered = agents;

    if (level) {
      filtered = filtered.filter(a => a.level === level);
    }
    if (department) {
      filtered = filtered.filter(a => a.department === department);
    }
    if (status) {
      filtered = filtered.filter(a => a.status === status);
    }

    // Non-master users only see their accessible agents
    if (!user.isMaster) {
      // In production, filter by department/team access
    }

    const total = filtered.length;
    const start = (page - 1) * limit;
    const paginated = filtered.slice(start, start + limit);

    return c.json({
      agents: paginated,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    });
  },

  async get(c: Context) {
    const agents = getAgentStore();
    const id = c.req.param('id');
    const agent = agents.find(a => a.id === id);

    if (!agent) {
      return c.json({ error: 'Agent not found' }, 404);
    }

    return c.json({ agent });
  },

  async create(c: Context) {
    const user = c.get('user');
    if (!user.isMaster) {
      return c.json({ error: 'Only master can create agents' }, 403);
    }

    const body = await c.req.json();
    const { parent_id, level, department, role, name, description, tools, skills, permissions, config } = body;

    // Validate parent exists
    const agents = getAgentStore();
    if (parent_id) {
      const parent = agents.find(a => a.id === parent_id);
      if (!parent) {
        return c.json({ error: 'Parent agent not found' }, 400);
      }
    }

    // Generate new agent ID
    const levelAgents = agents.filter(a => a.level === level).length;
    const newId = generateAgentId(level, levelAgents + 1);

    const newAgent: Agent = {
      id: newId,
      parent_id,
      level,
      department,
      role,
      name,
      description,
      system_prompt: getSystemPrompt(level, department, role),
      tools: tools || [],
      skills: skills || [],
      permissions: permissions || [],
      config: config || {},
      status: 'active',
      current_task_id: null,
      tasks_completed: 0,
      tasks_failed: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    agents.push(newAgent);
    return c.json({ agent: newAgent }, 201);
  },

  async update(c: Context) {
    const user = c.get('user');
    const agents = getAgentStore();
    const id = c.req.param('id');
    const agentIndex = agents.findIndex(a => a.id === id);

    if (agentIndex === -1) {
      return c.json({ error: 'Agent not found' }, 404);
    }

    // Only master or agent's direct manager can update
    if (!user.isMaster && agents[agentIndex].parent_id !== user.sub) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    const body = await c.req.json();
    const allowedFields = ['name', 'description', 'tools', 'skills', 'permissions', 'config', 'status'];

    for (const key of allowedFields) {
      if (body[key] !== undefined) {
        (agents[agentIndex] as any)[key] = body[key];
      }
    }

    agents[agentIndex].updated_at = new Date().toISOString();
    return c.json({ agent: agents[agentIndex] });
  },

  async delete(c: Context) {
    const user = c.get('user');
    if (!user.isMaster) {
      return c.json({ error: 'Only master can delete agents' }, 403);
    }

    const agents = getAgentStore();
    const id = c.req.param('id');
    const agentIndex = agents.findIndex(a => a.id === id);

    if (agentIndex === -1) {
      return c.json({ error: 'Agent not found' }, 404);
    }

    // Check for children
    const hasChildren = agents.some(a => a.parent_id === id);
    if (hasChildren) {
      return c.json({ error: 'Cannot delete agent with children. Delete children first.' }, 400);
    }

    agents.splice(agentIndex, 1);
    return c.json({ success: true });
  },

  async initializeHierarchy(c: Context) {
    const user = c.get('user');
    if (!user.isMaster) {
      return c.json({ error: 'Only master can initialize hierarchy' }, 403);
    }

    // Reset and regenerate
    agentStore = createAgentHierarchy();
    const total = agentStore.length;

    return c.json({
      success: true,
      message: `Initialized ${total} agents in hierarchy`,
      counts: {
        master: agentStore.filter(a => a.level === 1).length,
        principals: agentStore.filter(a => a.level === 2).length,
        heads: agentStore.filter(a => a.level === 3).length,
        team_leaders: agentStore.filter(a => a.level === 4).length,
        workers: agentStore.filter(a => a.level === 5).length,
      },
    });
  },
};