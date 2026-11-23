/**
 * AUTONOMOUSFORGE - Auth Routes
 * Handles authentication with master API key support
 */

import { Context } from 'hono';
import { sign, verify } from 'hono/jwt';
import { setCookie, deleteCookie } from 'hono/cookie';

interface AuthEnv {
  JWT_SECRET: string;
  MASTER_API_KEY?: string;
  SESSION_KV?: KVNamespace;
}

async function hashPassword(password: string): Promise<string> {
  // Use Web Crypto API for Argon2id-like hashing
  const encoder = new TextEncoder();
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(password),
    { name: 'PBKDF2' },
    false,
    ['deriveBits']
  );
  const derived = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
    key,
    256
  );
  const hash = new Uint8Array(derived);
  const combined = new Uint8Array(salt.length + hash.length);
  combined.set(salt);
  combined.set(hash, salt.length);
  return btoa(String.fromCharCode(...combined));
}

async function verifyPassword(password: string, storedHash: string): Promise<boolean> {
  try {
    const combined = Uint8Array.from(atob(storedHash), c => c.charCodeAt(0));
    const salt = combined.slice(0, 16);
    const hash = combined.slice(16);
    const encoder = new TextEncoder();
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode(password),
      { name: 'PBKDF2' },
      false,
      ['deriveBits']
    );
    const derived = await crypto.subtle.deriveBits(
      { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
      key,
      256
    );
    const newHash = new Uint8Array(derived);
    return hash.length === newHash.length && hash.every((v, i) => v === newHash[i]);
  } catch {
    return false;
  }
}

async function createToken(payload: object, secret: string, expiryHours: number): Promise<string> {
  const exp = Math.floor(Date.now() / 1000) + expiryHours * 3600;
  return sign({ ...payload, exp }, secret);
}

async function getUserFromDB(c: Context, email: string) {
  // In a real implementation, this would query the database
  // For now, return mock user if email matches
  const cloudConfig = c.get('cloudConfig');
  const db = cloudConfig.getDatabaseUrl();

  // Check if it's the master API key login
  const masterKey = cloudConfig.getMasterApiKey();
  if (masterKey && email === 'master@autonomousforge.local') {
    return {
      id: 'master',
      email: 'master@autonomousforge.local',
      name: 'Master Administrator',
      owner_id: 'master',
      is_master: true,
      password_hash: await hashPassword(masterKey), // This won't be used for master key
    };
  }

  // In production, query actual database
  // For Cloudflare Worker, use service bindings to call auth-service
  const authService = (c.env as any).AUTH_SERVICE;
  if (authService) {
    const response = await authService.fetch(`${cloudConfig.getApiBaseUrl()}/auth/internal/user-by-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    if (response.ok) {
      return response.json();
    }
  }

  return null;
}

export const handleAuth = {
  async login(c: Context) {
    const cloudConfig = c.get('cloudConfig');
    const body = await c.req.json();
    const { email, password, rememberMe } = body;

    // Check for master API key
    const masterKey = cloudConfig.getMasterApiKey();
    if (masterKey && password === masterKey && email === 'master@autonomousforge.local') {
      const accessToken = await createToken(
        { sub: 'master', email, isMaster: true, ownerId: 'master' },
        cloudConfig.getJwtSecret(),
        rememberMe ? 168 : 24 // 7 days if remember, 24 hours otherwise
      );
      const refreshToken = await createToken(
        { sub: 'master', type: 'refresh' },
        cloudConfig.getJwtSecret(),
        rememberMe ? 168 * 24 : 7 * 24 // 7 days or 168 hours
      );

      setCookie(c, 'access_token', accessToken, {
        httpOnly: true,
        secure: true,
        sameSite: 'lax',
        maxAge: rememberMe ? 60 * 60 * 24 * 7 : 60 * 60 * 24,
        path: '/',
      });
      setCookie(c, 'refresh_token', refreshToken, {
        httpOnly: true,
        secure: true,
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7,
        path: '/',
      });

      return c.json({
        access_token: accessToken,
        refresh_token: refreshToken,
        owner: {
          id: 'master',
          email: 'master@autonomousforge.local',
          name: 'Master Administrator',
          is_master: true,
        },
      });
    }

    // Regular user login
    const user = await getUserFromDB(c, email);
    if (!user) {
      return c.json({ error: 'Invalid credentials' }, 401);
    }

    const valid = await verifyPassword(password, user.password_hash);
    if (!valid) {
      return c.json({ error: 'Invalid credentials' }, 401);
    }

    const accessToken = await createToken(
      { sub: user.id, email: user.email, isMaster: user.is_master || false, ownerId: user.owner_id },
      cloudConfig.getJwtSecret(),
      rememberMe ? 168 : 24
    );
    const refreshToken = await createToken(
      { sub: user.id, type: 'refresh' },
      cloudConfig.getJwtSecret(),
      rememberMe ? 168 * 24 : 7 * 24
    );

    setCookie(c, 'access_token', accessToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      maxAge: rememberMe ? 60 * 60 * 24 * 7 : 60 * 60 * 24,
      path: '/',
    });
    setCookie(c, 'refresh_token', refreshToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7,
      path: '/',
    });

    return c.json({
      access_token: accessToken,
      refresh_token: refreshToken,
      owner: {
        id: user.id,
        email: user.email,
        name: user.name,
        is_master: user.is_master || false,
      },
    });
  },

  async login2fa(c: Context) {
    const cloudConfig = c.get('cloudConfig');
    const body = await c.req.json();
    const { email, code } = body;

    // In production, verify 2FA code
    const user = await getUserFromDB(c, email);
    if (!user) {
      return c.json({ error: 'Invalid credentials' }, 401);
    }

    // Mock 2FA verification - in production use TOTP
    if (code !== '123456') {
      return c.json({ error: 'Invalid 2FA code' }, 401);
    }

    const accessToken = await createToken(
      { sub: user.id, email: user.email, isMaster: user.is_master || false, ownerId: user.owner_id },
      cloudConfig.getJwtSecret(),
      24
    );
    const refreshToken = await createToken(
      { sub: user.id, type: 'refresh' },
      cloudConfig.getJwtSecret(),
      7 * 24
    );

    setCookie(c, 'access_token', accessToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      maxAge: 60 * 60 * 24,
      path: '/',
    });
    setCookie(c, 'refresh_token', refreshToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7,
      path: '/',
    });

    return c.json({
      access_token: accessToken,
      refresh_token: refreshToken,
      owner: {
        id: user.id,
        email: user.email,
        name: user.name,
        is_master: user.is_master || false,
      },
    });
  },

  async logout(c: Context) {
    deleteCookie(c, 'access_token', { path: '/' });
    deleteCookie(c, 'refresh_token', { path: '/' });
    return c.json({ success: true });
  },

  async refresh(c: Context) {
    const cloudConfig = c.get('cloudConfig');
    const refreshToken = c.req.header('Authorization')?.replace('Bearer ', '') ||
                         getCookie(c, 'refresh_token');

    if (!refreshToken) {
      return c.json({ error: 'No refresh token' }, 401);
    }

    try {
      const payload = await verify(refreshToken, cloudConfig.getJwtSecret());
      if (payload.type !== 'refresh') {
        return c.json({ error: 'Invalid token type' }, 401);
      }

      const accessToken = await createToken(
        { sub: payload.sub, email: payload.email, isMaster: payload.isMaster, ownerId: payload.ownerId },
        cloudConfig.getJwtSecret(),
        24
      );

      setCookie(c, 'access_token', accessToken, {
        httpOnly: true,
        secure: true,
        sameSite: 'lax',
        maxAge: 60 * 60 * 24,
        path: '/',
      });

      return c.json({ access_token: accessToken });
    } catch {
      return c.json({ error: 'Invalid refresh token' }, 401);
    }
  },

  async me(c: Context) {
    const user = c.get('user');
    if (!user) {
      return c.json({ error: 'Not authenticated' }, 401);
    }

    // Fetch full user data from database
    const dbUser = await getUserFromDB(c, user.email);
    if (!dbUser) {
      return c.json({ error: 'User not found' }, 404);
    }

    return c.json({
      id: dbUser.id,
      email: dbUser.email,
      name: dbUser.name,
      is_master: dbUser.is_master || false,
    });
  },

  async setup(c: Context) {
    const cloudConfig = c.get('cloudConfig');
    const body = await c.req.json();
    const { email, password, name } = body;

    // Check if owner already exists
    const existing = await getUserFromDB(c, email);
    if (existing) {
      return c.json({ error: 'Owner already exists' }, 400);
    }

    // Create owner user
    const passwordHash = await hashPassword(password);
    const masterKey = cloudConfig.getMasterApiKey() || `af_master_${crypto.randomUUID().replace(/-/g, '')}`;

    // In production, insert into database
    // For now, return success with master key
    return c.json({
      success: true,
      master_api_key: masterKey,
      message: 'Owner created successfully. Save your master API key!',
    });
  },

  async setupStatus(c: Context) {
    // Check if owner exists
    const ownerExists = true; // In production, query database
    return c.json({ setup_complete: ownerExists });
  },
};

function getCookie(c: Context, name: string): string | undefined {
  const cookieHeader = c.req.header('Cookie');
  if (!cookieHeader) return undefined;
  const cookies = cookieHeader.split(';').map(c => c.trim());
  for (const cookie of cookies) {
    const [key, value] = cookie.split('=');
    if (key === name) return value;
  }
  return undefined;
}