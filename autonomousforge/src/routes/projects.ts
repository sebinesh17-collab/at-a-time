/**
 * AUTONOMOUSFORGE - Project Routes
 */

import { Context } from 'hono';

interface Project {
  id: string;
  owner_id: string;
  name: string;
  description: string;
  status: 'active' | 'archived' | 'completed';
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
}

let projectStore: Project[] = [];

function generateProjectId(): string {
  return `proj-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export const handleProjects = {
  async list(c: Context) {
    const user = c.get('user');
    const page = parseInt(c.req.query('page') || '1');
    const limit = parseInt(c.req.query('limit') || '20');
    const status = c.req.query('status');

    let filtered = projectStore;

    if (status) filtered = filtered.filter(p => p.status === status);

    // Non-master users see only their projects
    if (!user.isMaster) {
      filtered = filtered.filter(p => p.owner_id === user.ownerId);
    }

    const total = filtered.length;
    const start = (page - 1) * limit;
    const paginated = filtered.slice(start, start + limit);

    return c.json({
      projects: paginated,
      pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
    });
  },

  async get(c: Context) {
    const user = c.get('user');
    const id = c.req.param('id');
    const project = projectStore.find(p => p.id === id);

    if (!project) {
      return c.json({ error: 'Project not found' }, 404);
    }

    if (!user.isMaster && project.owner_id !== user.ownerId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    return c.json({ project });
  },

  async create(c: Context) {
    const user = c.get('user');
    const body = await c.req.json();
    const { name, description = '', settings = {} } = body;

    if (!name) {
      return c.json({ error: 'Project name is required' }, 400);
    }

    const project: Project = {
      id: generateProjectId(),
      owner_id: user.ownerId,
      name,
      description,
      status: 'active',
      settings,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    projectStore.push(project);
    return c.json({ project }, 201);
  },

  async update(c: Context) {
    const user = c.get('user');
    const id = c.req.param('id');
    const projectIndex = projectStore.findIndex(p => p.id === id);

    if (projectIndex === -1) {
      return c.json({ error: 'Project not found' }, 404);
    }

    const project = projectStore[projectIndex];

    if (!user.isMaster && project.owner_id !== user.ownerId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    const body = await c.req.json();
    const allowedFields = ['name', 'description', 'status', 'settings'];

    for (const key of allowedFields) {
      if (body[key] !== undefined) {
        (project as any)[key] = body[key];
      }
    }

    project.updated_at = new Date().toISOString();
    return c.json({ project });
  },

  async delete(c: Context) {
    const user = c.get('user');
    const id = c.req.param('id');
    const projectIndex = projectStore.findIndex(p => p.id === id);

    if (projectIndex === -1) {
      return c.json({ error: 'Project not found' }, 404);
    }

    const project = projectStore[projectIndex];

    if (!user.isMaster && project.owner_id !== user.ownerId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    projectStore.splice(projectIndex, 1);
    return c.json({ success: true });
  },
};