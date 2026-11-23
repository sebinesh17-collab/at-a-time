/**
 * AUTONOMOUSFORGE - Task Routes
 * DAG-based task decomposition (7 levels)
 */

import { Context } from 'hono';

type TaskLevel = 'project' | 'epic' | 'feature' | 'task' | 'subtask' | 'microtask' | 'atomic';
type TaskStatus = 'pending' | 'in_progress' | 'review' | 'completed' | 'failed' | 'blocked';

interface Task {
  id: string;
  parent_id: string | null;
  level: TaskLevel;
  level_index: number;
  title: string;
  description: string;
  assignee_id: string | null;
  status: TaskStatus;
  priority: number;
  dependencies: string[];
  dag_position: { x: number; y: number };
  estimated_effort: number;
  actual_effort: number;
  tags: string[];
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

const LEVEL_ORDER: TaskLevel[] = ['project', 'epic', 'feature', 'task', 'subtask', 'microtask', 'atomic'];
const LEVEL_INDEX: Record<TaskLevel, number> = {
  project: 0, epic: 1, feature: 2, task: 3, subtask: 4, microtask: 5, atomic: 6,
};

let taskStore: Task[] = [];
let taskIdCounter = 0;

function generateTaskId(): string {
  taskIdCounter++;
  return `task-${Date.now()}-${taskIdCounter}`;
}

function validateDag(task: Task, allTasks: Task[]): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Check dependencies exist
  for (const depId of task.dependencies) {
    if (!allTasks.some(t => t.id === depId)) {
      errors.push(`Dependency ${depId} does not exist`);
    }
  }

  // Check no circular dependencies
  const visited = new Set<string>();
  const visiting = new Set<string>();

  function visit(tid: string): boolean {
    if (visiting.has(tid)) return false; // Cycle detected
    if (visited.has(tid)) return true;
    visiting.add(tid);
    const t = allTasks.find(x => x.id === tid);
    if (t) {
      for (const dep of t.dependencies) {
        if (!visit(dep)) return false;
      }
    }
    visiting.delete(tid);
    visited.add(tid);
    return true;
  }

  if (!visit(task.id)) {
    errors.push('Circular dependency detected');
  }

  // Check level hierarchy (parent must be higher level)
  if (task.parent_id) {
    const parent = allTasks.find(t => t.id === task.parent_id);
    if (parent && LEVEL_INDEX[parent.level] >= LEVEL_INDEX[task.level]) {
      errors.push('Parent task must be higher level in hierarchy');
    }
  }

  return { valid: errors.length === 0, errors };
}

export const handleTasks = {
  async list(c: Context) {
    const user = c.get('user');
    const page = parseInt(c.req.query('page') || '1');
    const limit = parseInt(c.req.query('limit') || '50');
    const level = c.req.query('level') as TaskLevel | undefined;
    const status = c.req.query('status') as TaskStatus | undefined;
    const assigneeId = c.req.query('assignee_id');

    let filtered = taskStore;

    if (level) filtered = filtered.filter(t => t.level === level);
    if (status) filtered = filtered.filter(t => t.status === status);
    if (assigneeId) filtered = filtered.filter(t => t.assignee_id === assigneeId);

    // Non-master users see only their assigned tasks
    if (!user.isMaster) {
      filtered = filtered.filter(t => t.assignee_id === user.sub);
    }

    const total = filtered.length;
    const start = (page - 1) * limit;
    const paginated = filtered.slice(start, start + limit);

    return c.json({
      tasks: paginated,
      pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
    });
  },

  async get(c: Context) {
    const id = c.req.param('id');
    const task = taskStore.find(t => t.id === id);

    if (!task) {
      return c.json({ error: 'Task not found' }, 404);
    }

    // Include children for tree view
    const children = taskStore.filter(t => t.parent_id === id);

    return c.json({ task, children });
  },

  async create(c: Context) {
    const user = c.get('user');
    const body = await c.req.json();

    const {
      parent_id,
      level,
      title,
      description = '',
      assignee_id,
      priority = 0,
      dependencies = [],
      estimated_effort = 0,
      tags = [],
      metadata = {},
    } = body;

    // Validate level
    if (!LEVEL_ORDER.includes(level)) {
      return c.json({ error: 'Invalid task level' }, 400);
    }

    // Validate parent
    if (parent_id) {
      const parent = taskStore.find(t => t.id === parent_id);
      if (!parent) {
        return c.json({ error: 'Parent task not found' }, 400);
      }
      if (LEVEL_INDEX[parent.level] >= LEVEL_INDEX[level]) {
        return c.json({ error: 'Parent must be higher level' }, 400);
      }
    }

    // Check permissions for assignee
    if (assignee_id && !user.isMaster) {
      // In production, verify user can assign to this agent
    }

    const task: Task = {
      id: generateTaskId(),
      parent_id: parent_id || null,
      level,
      level_index: LEVEL_INDEX[level],
      title,
      description,
      assignee_id: assignee_id || null,
      status: 'pending',
      priority,
      dependencies,
      dag_position: { x: 0, y: 0 },
      estimated_effort,
      actual_effort: 0,
      tags,
      metadata,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      completed_at: null,
    };

    const validation = validateDag(task, [...taskStore, task]);
    if (!validation.valid) {
      return c.json({ error: 'Invalid DAG', details: validation.errors }, 400);
    }

    taskStore.push(task);
    return c.json({ task }, 201);
  },

  async update(c: Context) {
    const user = c.get('user');
    const id = c.req.param('id');
    const taskIndex = taskStore.findIndex(t => t.id === id);

    if (taskIndex === -1) {
      return c.json({ error: 'Task not found' }, 404);
    }

    const task = taskStore[taskIndex];

    // Check permissions
    if (!user.isMaster && task.assignee_id !== user.sub) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    const body = await c.req.json();
    const allowedFields = [
      'title', 'description', 'assignee_id', 'status', 'priority',
      'dependencies', 'dag_position', 'estimated_effort', 'actual_effort',
      'tags', 'metadata',
    ];

    const updatedTask = { ...task };
    for (const key of allowedFields) {
      if (body[key] !== undefined) {
        (updatedTask as any)[key] = body[key];
      }
    }

    // Handle status transitions
    if (body.status === 'completed' && task.status !== 'completed') {
      updatedTask.completed_at = new Date().toISOString();
    } else if (body.status !== 'completed' && task.status === 'completed') {
      updatedTask.completed_at = null;
    }

    updatedTask.updated_at = new Date().toISOString();

    const validation = validateDag(updatedTask, taskStore.map((t, i) => i === taskIndex ? updatedTask : t));
    if (!validation.valid) {
      return c.json({ error: 'Invalid DAG', details: validation.errors }, 400);
    }

    taskStore[taskIndex] = updatedTask;
    return c.json({ task: updatedTask });
  },

  async delete(c: Context) {
    const user = c.get('user');
    const id = c.req.param('id');
    const taskIndex = taskStore.findIndex(t => t.id === id);

    if (taskIndex === -1) {
      return c.json({ error: 'Task not found' }, 404);
    }

    // Check for children
    const hasChildren = taskStore.some(t => t.parent_id === id);
    if (hasChildren) {
      return c.json({ error: 'Cannot delete task with children' }, 400);
    }

    // Check if other tasks depend on this
    const hasDependents = taskStore.some(t => t.dependencies.includes(id));
    if (hasDependents) {
      return c.json({ error: 'Cannot delete task with dependents' }, 400);
    }

    if (!user.isMaster) {
      return c.json({ error: 'Only master can delete tasks' }, 403);
    }

    taskStore.splice(taskIndex, 1);
    return c.json({ success: true });
  },

  async execute(c: Context) {
    const user = c.get('user');
    const id = c.req.param('id');
    const task = taskStore.find(t => t.id === id);

    if (!task) {
      return c.json({ error: 'Task not found' }, 404);
    }

    // Check if all dependencies are completed
    const incompleteDeps = task.dependencies.filter(depId => {
      const dep = taskStore.find(t => t.id === depId);
      return dep && dep.status !== 'completed';
    });

    if (incompleteDeps.length > 0) {
      return c.json({
        error: 'Dependencies not completed',
        incompleteDependencies: incompleteDeps,
      }, 400);
    }

    // Check assignee
    if (task.assignee_id && task.assignee_id !== user.sub && !user.isMaster) {
      return c.json({ error: 'Not assigned to you' }, 403);
    }

    // Update status to in_progress
    task.status = 'in_progress';
    task.updated_at = new Date().toISOString();

    // In production, trigger actual execution via service binding
    // For now, simulate execution
    const result = {
      taskId: task.id,
      status: 'started',
      message: 'Task execution started',
      estimatedCompletion: new Date(Date.now() + task.estimated_effort * 60000).toISOString(),
    };

    return c.json(result);
  },

  // Get DAG structure for visualization
  async getDag(c: Context) {
    const projectId = c.req.query('project_id');
    let tasks = taskStore;

    if (projectId) {
      // Get all tasks in this project's hierarchy
      const project = taskStore.find(t => t.id === projectId && t.level === 'project');
      if (!project) {
        return c.json({ error: 'Project not found' }, 404);
      }

      const getDescendants = (parentId: string): Task[] => {
        const children = taskStore.filter(t => t.parent_id === parentId);
        let result = [...children];
        for (const child of children) {
          result.push(...getDescendants(child.id));
        }
        return result;
      };

      tasks = [project, ...getDescendants(projectId)];
    }

    // Build nodes and edges for DAG visualization
    const nodes = tasks.map(t => ({
      id: t.id,
      label: t.title,
      level: t.level,
      status: t.status,
      assignee: t.assignee_id,
      position: t.dag_position,
    }));

    const edges = tasks.flatMap(t =>
      t.dependencies.map(depId => ({ from: depId, to: t.id }))
    );

    return c.json({ nodes, edges });
  },
};