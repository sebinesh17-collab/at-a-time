/**
 * AUTONOMOUSFORGE - Health Check Route
 */

import { Context } from 'hono';

export async function handleHealth(c: Context) {
  const cloudConfig = c.get('cloudConfig');
  const config = cloudConfig.getConfig();

  return c.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    environment: config.isCloudflare ? 'cloudflare' : 'local',
    deployment: config.isCloudflarePages ? 'pages' : (config.isCloudflareWorker ? 'worker' : 'local'),
    database: config.databaseType,
    theme: config.themeMode,
    bindings: {
      kv: config.kvEnabled,
      r2: config.r2Enabled,
      d1: config.databaseType === 'd1',
      hyperdrive: config.databaseType === 'hyperdrive',
      workersAI: config.workersAIEnabled,
    },
  });
}