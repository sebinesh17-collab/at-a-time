/**
 * AUTONOMOUSFORGE - Chat Routes
 * Handles AI chat sessions with agent integration
 */

import { Context } from 'hono';

interface ChatSession {
  id: string;
  owner_id: string;
  title: string;
  agent_id: string | null;
  model: string;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_calls: any[];
  tool_call_id: string | null;
  metadata: Record<string, any>;
  created_at: string;
}

let sessionStore: ChatSession[] = [];
let messageStore: ChatMessage[] = [];

function generateSessionId(): string {
  return `chat-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function generateMessageId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export const handleChat = {
  async listSessions(c: Context) {
    const user = c.get('user');
    const page = parseInt(c.req.query('page') || '1');
    const limit = parseInt(c.req.query('limit') || '20');

    let filtered = sessionStore;

    if (!user.isMaster) {
      filtered = filtered.filter(s => s.owner_id === user.ownerId);
    }

    // Sort by updated_at descending
    filtered.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());

    const total = filtered.length;
    const start = (page - 1) * limit;
    const paginated = filtered.slice(start, start + limit);

    return c.json({
      sessions: paginated,
      pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
    });
  },

  async createSession(c: Context) {
    const user = c.get('user');
    const body = await c.req.json();
    const { title = 'New Chat', agent_id, model = 'nemotron-3-ultra', settings = {} } = body;

    const session: ChatSession = {
      id: generateSessionId(),
      owner_id: user.ownerId,
      title,
      agent_id: agent_id || null,
      model,
      settings,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    sessionStore.push(session);
    return c.json({ session }, 201);
  },

  async getSession(c: Context) {
    const user = c.get('user');
    const id = c.req.param('id');
    const session = sessionStore.find(s => s.id === id);

    if (!session) {
      return c.json({ error: 'Session not found' }, 404);
    }

    if (!user.isMaster && session.owner_id !== user.ownerId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    return c.json({ session });
  },

  async sendMessage(c: Context) {
    const user = c.get('user');
    const sessionId = c.req.param('id');
    const session = sessionStore.find(s => s.id === sessionId);

    if (!session) {
      return c.json({ error: 'Session not found' }, 404);
    }

    if (!user.isMaster && session.owner_id !== user.ownerId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    const body = await c.req.json();
    const { content, role = 'user' } = body;

    if (!content) {
      return c.json({ error: 'Message content is required' }, 400);
    }

    // Create user message
    const userMessage: ChatMessage = {
      id: generateMessageId(),
      session_id: sessionId,
      role,
      content,
      tool_calls: [],
      tool_call_id: null,
      metadata: {},
      created_at: new Date().toISOString(),
    };

    messageStore.push(userMessage);

    // In production, call model-gateway or Workers AI
    // For now, generate a mock response
    const assistantMessage: ChatMessage = {
      id: generateMessageId(),
      session_id: sessionId,
      role: 'assistant',
      content: `I received your message: "${content}". This is a mock response. In production, this would call NVIDIA NIM (${session.model}) or Workers AI.`,
      tool_calls: [],
      tool_call_id: null,
      metadata: { model: session.model },
      created_at: new Date().toISOString(),
    };

    messageStore.push(assistantMessage);

    // Update session
    session.updated_at = new Date().toISOString();
    if (session.messages.length === 1) {
      session.title = content.slice(0, 50);
    }

    return c.json({
      userMessage,
      assistantMessage,
    });
  },

  async getMessages(c: Context) {
    const user = c.get('user');
    const sessionId = c.req.param('id');
    const session = sessionStore.find(s => s.id === sessionId);

    if (!session) {
      return c.json({ error: 'Session not found' }, 404);
    }

    if (!user.isMaster && session.owner_id !== user.ownerId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    const page = parseInt(c.req.query('page') || '1');
    const limit = parseInt(c.req.query('limit') || '50');

    let messages = messageStore.filter(m => m.session_id === sessionId);
    messages.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

    const total = messages.length;
    const start = (page - 1) * limit;
    const paginated = messages.slice(start, start + limit);

    return c.json({
      messages: paginated,
      pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
    });
  },
};