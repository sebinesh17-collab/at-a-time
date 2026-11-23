/**
 * AUTONOMOUSFORGE - Cloudflare Worker Entry Point
 * API Gateway with auth, routing, rate limiting, and cloud config
 */

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { secureHeaders } from 'hono/secure-headers';
import { rateLimiter } from 'hono-rate-limiter';
import { jwt } from 'hono/jwt';
import { logger } from 'hono/logger';
import { handleAuth } from './routes/auth';
import { handleAgents } from './routes/agents';
import { handleTasks } from './routes/tasks';
import { handleProjects } from './routes/projects';
import { handleChat } from './routes/chat';
import { handleHealth } from './routes/health';
import { CloudConfig } from './cloud-config';

type Bindings = {
  SESSION_KV: KVNamespace;
  FILE_STORAGE: R2Bucket;
  DB?: D1Database;
  HYPERDRIVE?: Hyperdrive;
  AI?: Ai;
  AUTH_SERVICE?: Fetcher;
  AGENT_REGISTRY?: Fetcher;
  MASTER_ORCHESTRATOR?: Fetcher;
  TASK_SCHEDULER?: Fetcher;
  MODEL_GATEWAY?: Fetcher;
  PROVIDER_SERVICE?: Fetcher;
  FILE_SERVICE?: Fetcher;
  MEMORY_SERVICE?: Fetcher;
  KNOWLEDGE_SERVICE?: Fetcher;
  EXECUTION_SERVICE?: Fetcher;
  BUILD_SERVICE?: Fetcher;
  TESTING_SERVICE?: Fetcher;
  MONITORING_SERVICE?: Fetcher;
};

type Variables = {
  user: { id: string; email: string; isMaster: boolean; ownerId: string };
  cloudConfig: CloudConfig;
};

const app = new Hono<{ Bindings: Bindings; Variables: Variables }>();

// Global middleware
app.use('*', logger());
app.use('*', secureHeaders());
app.use('*', cors({
  origin: ['https://*.pages.dev', 'https://autonomousforge.yourdomain.com', 'http://localhost:3000'],
  allowHeaders: ['Content-Type', 'Authorization', 'X-Cloud-Config'],
  allowMethods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  exposeHeaders: ['X-Cloud-Config'],
  credentials: true,
}));

// Rate limiting
app.use('/api/*', rateLimiter({
  windowMs: 60 * 1000,
  limit: 100,
  keyGenerator: (c) => c.req.header('cf-connecting-ip') || 'unknown',
}));

// Cloud configuration middleware
app.use('*', async (c, next) => {
  const cloudConfig = new CloudConfig(c.env);
  await cloudConfig.detect();
  c.set('cloudConfig', cloudConfig);

  // Add cloud config headers to responses
  c.res.headers.set('X-Cloud-Config', JSON.stringify({
    theme: cloudConfig.getVisualTheme(),
    features: cloudConfig.getFeatureFlags(),
    database: cloudConfig.getDatabaseType(),
  }));

  await next();
});

// Health check (no auth required)
app.get('/health', handleHealth);
app.get('/api/health', handleHealth);

// Cloud config endpoint (no auth required)
app.get('/api/cloud-config', (c) => {
  const cloudConfig = c.get('cloudConfig');
  return c.json({
    theme: cloudConfig.getVisualTheme(),
    features: cloudConfig.getFeatureFlags(),
    database: cloudConfig.getDatabaseType(),
    endpoints: {
      api: cloudConfig.getApiBaseUrl(),
      ws: cloudConfig.getWsBaseUrl(),
    },
  });
});

// Auth routes
app.post('/api/auth/login', handleAuth.login);
app.post('/api/auth/login/2fa', handleAuth.login2fa);
app.post('/api/auth/logout', handleAuth.logout);
app.post('/api/auth/refresh', handleAuth.refresh);
app.get('/api/auth/me', handleAuth.me);
app.post('/api/auth/setup', handleAuth.setup);
app.get('/api/auth/setup/status', handleAuth.setupStatus);

// Protected routes - require authentication
const authMiddleware = jwt({ secret: c.env.JWT_SECRET || 'default-secret-change-me' });

app.use('/api/agents/*', authMiddleware);
app.use('/api/tasks/*', authMiddleware);
app.use('/api/projects/*', authMiddleware);
app.use('/api/chat/*', authMiddleware);

// Agent routes
app.get('/api/agents', handleAgents.list);
app.post('/api/agents', handleAgents.create);
app.get('/api/agents/:id', handleAgents.get);
app.patch('/api/agents/:id', handleAgents.update);
app.delete('/api/agents/:id', handleAgents.delete);
app.post('/api/agents/initialize', handleAgents.initializeHierarchy);

// Task routes
app.get('/api/tasks', handleTasks.list);
app.post('/api/tasks', handleTasks.create);
app.get('/api/tasks/:id', handleTasks.get);
app.patch('/api/tasks/:id', handleTasks.update);
app.delete('/api/tasks/:id', handleTasks.delete);
app.post('/api/tasks/:id/execute', handleTasks.execute);

// Project routes
app.get('/api/projects', handleProjects.list);
app.post('/api/projects', handleProjects.create);
app.get('/api/projects/:id', handleProjects.get);
app.patch('/api/projects/:id', handleProjects.update);
app.delete('/api/projects/:id', handleProjects.delete);

// Chat routes
app.get('/api/chat/sessions', handleChat.listSessions);
app.post('/api/chat/sessions', handleChat.createSession);
app.get('/api/chat/sessions/:id', handleChat.getSession);
app.post('/api/chat/sessions/:id/messages', handleChat.sendMessage);
app.get('/api/chat/sessions/:id/messages', handleChat.getMessages);

// 404 handler
app.notFound((c) => c.json({ error: 'Not found' }, 404));

// Error handler
app.onError((err, c) => {
  console.error('Worker error:', err);
  return c.json({ error: 'Internal server error' }, 500);
});

export default app;
export type { Bindings, Variables };