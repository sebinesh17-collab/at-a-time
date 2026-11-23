/**
 * AUTONOMOUSFORGE - Cloudflare Worker Cloud Configuration
 * Auto-detects environment and configures database, bindings, themes, endpoints
 */

export interface CloudflareEnv {
  // KV Namespaces
  SESSION_KV?: KVNamespace;

  // R2 Buckets
  FILE_STORAGE?: R2Bucket;

  // D1 Databases
  DB?: D1Database;

  // Hyperdrive
  HYPERDRIVE?: Hyperdrive;

  // Workers AI
  AI?: Ai;

  // Service Bindings
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

  // Environment Variables
  JWT_SECRET?: string;
  DATABASE_URL?: string;
  REDIS_URL?: string;
  API_DOMAIN?: string;
  FRONTEND_URL?: string;
  THEME_MODE?: string;
  PRIMARY_COLOR?: string;
  ACCENT_COLOR?: string;
  BACKGROUND_COLOR?: string;
  SURFACE_COLOR?: string;
  MASTER_API_KEY?: string;
  NVIDIA_NIM_API_KEY?: string;
  NVIDIA_NIM_MODEL?: string;
  NVIDIA_NIM_BASE_URL?: string;
  CF_ACCOUNT_ID?: string;
  CF_PAGES?: string;
  CF_WORKER?: string;
}

export interface VisualTheme {
  themeMode: 'purple' | 'dark' | 'light' | 'cloudflare';
  primaryColor: string;
  accentColor: string;
  backgroundColor: string;
  surfaceColor: string;
  isCloudflare: boolean;
}

export interface FeatureFlags {
  backgroundSync: boolean;
  pushNotifications: boolean;
  offlineSupport: boolean;
  serviceWorker: boolean;
  workersAI: boolean;
  kv: boolean;
  r2: boolean;
  d1: boolean;
  hyperdrive: boolean;
}

export interface CloudConfigData {
  isCloudflare: boolean;
  isCloudflarePages: boolean;
  isCloudflareWorker: boolean;
  isLocal: boolean;
  databaseType: 'postgresql' | 'd1' | 'hyperdrive';
  d1DatabaseId: string | null;
  hyperdriveEnabled: boolean;
  kvEnabled: boolean;
  r2Enabled: boolean;
  workersAIEnabled: boolean;
  themeMode: 'purple' | 'dark' | 'light' | 'cloudflare' | 'auto';
  primaryColor: string;
  accentColor: string;
  backgroundColor: string;
  surfaceColor: string;
  apiBaseUrl: string;
  wsBaseUrl: string;
  frontendUrl: string;
  apiDomain: string;
  enableBackgroundSync: boolean;
  enablePushNotifications: boolean;
  enableOfflineSupport: boolean;
  enableServiceWorker: boolean;
}

export class CloudConfig {
  private config: CloudConfigData | null = null;
  private initialized = false;
  private env: CloudflareEnv;

  constructor(env: CloudflareEnv) {
    this.env = env;
  }

  async detect(): Promise<CloudConfigData> {
    if (this.initialized && this.config) {
      return this.config;
    }

    const env = this.env;
    const isPages = env.CF_PAGES === 'true' || typeof (globalThis as any).PAGES !== 'undefined';
    const isWorker = env.CF_WORKER === 'true' || !isPages && (env.CF_ACCOUNT_ID || env.SESSION_KV || env.DB || env.HYPERDRIVE || env.AI);
    const isCloudflare = isPages || isWorker;
    const isLocal = !isCloudflare;

    // Determine database type
    let databaseType: 'postgresql' | 'd1' | 'hyperdrive' = 'postgresql';
    let d1DatabaseId: string | null = null;
    let hyperdriveEnabled = false;

    if (env.DB) {
      databaseType = 'd1';
      d1DatabaseId = env.DB.name;
    } else if (env.HYPERDRIVE) {
      databaseType = 'hyperdrive';
      hyperdriveEnabled = true;
    } else if (env.DATABASE_URL) {
      // Check if it's a Hyperdrive URL
      if (env.DATABASE_URL.includes('.hyperdrive.cloudflare.com')) {
        databaseType = 'hyperdrive';
        hyperdriveEnabled = true;
      }
    }

    // Determine feature flags
    const kvEnabled = !!env.SESSION_KV;
    const r2Enabled = !!env.FILE_STORAGE;
    const workersAIEnabled = !!env.AI;

    // Determine visual theme
    let themeMode: 'purple' | 'dark' | 'light' | 'cloudflare' | 'auto' = 'purple';
    let primaryColor = '#7c3aed';
    let accentColor = '#a855f7';
    let backgroundColor = '#0f172a';
    let surfaceColor = '#1e293b';

    if (isCloudflare) {
      // Check for custom theme from env
      if (env.THEME_MODE) {
        themeMode = env.THEME_MODE as any;
      } else {
        themeMode = 'cloudflare';
      }

      if (themeMode === 'cloudflare') {
        primaryColor = env.PRIMARY_COLOR || '#f97316'; // Cloudflare Orange
        accentColor = env.ACCENT_COLOR || '#fb923c';
        backgroundColor = env.BACKGROUND_COLOR || '#0f172a';
        surfaceColor = env.SURFACE_COLOR || '#1e293b';
      } else if (themeMode === 'purple') {
        primaryColor = env.PRIMARY_COLOR || '#7c3aed';
        accentColor = env.ACCENT_COLOR || '#a855f7';
        backgroundColor = env.BACKGROUND_COLOR || '#0f172a';
        surfaceColor = env.SURFACE_COLOR || '#1e293b';
      } else if (themeMode === 'dark') {
        primaryColor = env.PRIMARY_COLOR || '#6366f1';
        accentColor = env.ACCENT_COLOR || '#818cf8';
        backgroundColor = env.BACKGROUND_COLOR || '#020617';
        surfaceColor = env.SURFACE_COLOR || '#0f172a';
      } else if (themeMode === 'light') {
        primaryColor = env.PRIMARY_COLOR || '#7c3aed';
        accentColor = env.ACCENT_COLOR || '#a855f7';
        backgroundColor = env.BACKGROUND_COLOR || '#f8fafc';
        surfaceColor = env.SURFACE_COLOR || '#ffffff';
      }
    }

    // Determine API endpoints
    let apiBaseUrl = '/api';
    let wsBaseUrl = '/ws';
    let frontendUrl = env.FRONTEND_URL || '';
    let apiDomain = env.API_DOMAIN || '';

    if (isCloudflare && apiDomain) {
      apiBaseUrl = `https://${apiDomain}/api`;
      wsBaseUrl = `wss://${apiDomain}/ws`;
    } else if (isPages && env.FRONTEND_URL) {
      // Frontend on Pages, API on custom domain
      const frontendOrigin = new URL(env.FRONTEND_URL).origin;
      if (apiDomain) {
        apiBaseUrl = `https://${apiDomain}/api`;
        wsBaseUrl = `wss://${apiDomain}/ws`;
      } else {
        apiBaseUrl = `${frontendOrigin}/api`;
        wsBaseUrl = `${frontendOrigin.replace('https:', 'wss:')}/ws`;
      }
      frontendUrl = env.FRONTEND_URL;
    } else if (isWorker) {
      // Worker deployment - API is this worker
      const workerUrl = `https://${env.CF_ACCOUNT_ID}.workers.dev`; // Will be overridden by custom domain
      if (apiDomain) {
        apiBaseUrl = `https://${apiDomain}/api`;
        wsBaseUrl = `wss://${apiDomain}/ws`;
      }
    } else {
      // Local development
      frontendUrl = 'http://localhost:3000';
      apiBaseUrl = '/api';
      wsBaseUrl = '/ws';
    }

    this.config = {
      isCloudflare,
      isCloudflarePages: isPages,
      isCloudflareWorker: isWorker,
      isLocal,
      databaseType,
      d1DatabaseId,
      hyperdriveEnabled,
      kvEnabled,
      r2Enabled,
      workersAIEnabled,
      themeMode,
      primaryColor,
      accentColor,
      backgroundColor,
      surfaceColor,
      apiBaseUrl,
      wsBaseUrl,
      frontendUrl,
      apiDomain,
      enableBackgroundSync: true,
      enablePushNotifications: true,
      enableOfflineSupport: true,
      enableServiceWorker: true,
    };

    this.initialized = true;
    return this.config;
  }

  getConfig(): CloudConfigData {
    if (!this.initialized || !this.config) {
      throw new Error('CloudConfig not initialized. Call detect() first.');
    }
    return this.config;
  }

  getApiBaseUrl(): string {
    return this.getConfig().apiBaseUrl;
  }

  getWsBaseUrl(): string {
    return this.getConfig().wsBaseUrl;
  }

  getVisualTheme(): VisualTheme {
    const cfg = this.getConfig();
    return {
      themeMode: cfg.themeMode,
      primaryColor: cfg.primaryColor,
      accentColor: cfg.accentColor,
      backgroundColor: cfg.backgroundColor,
      surfaceColor: cfg.surfaceColor,
      isCloudflare: cfg.isCloudflare,
    };
  }

  getFeatureFlags(): FeatureFlags {
    const cfg = this.getConfig();
    return {
      backgroundSync: cfg.enableBackgroundSync,
      pushNotifications: cfg.enablePushNotifications,
      offlineSupport: cfg.enableOfflineSupport,
      serviceWorker: cfg.enableServiceWorker,
      workersAI: cfg.workersAIEnabled,
      kv: cfg.kvEnabled,
      r2: cfg.r2Enabled,
      d1: cfg.databaseType === 'd1',
      hyperdrive: cfg.databaseType === 'hyperdrive',
    };
  }

  getDatabaseType(): 'postgresql' | 'd1' | 'hyperdrive' {
    return this.getConfig().databaseType;
  }

  isCloudflare(): boolean {
    return this.getConfig().isCloudflare;
  }

  isLocal(): boolean {
    return this.getConfig().isLocal;
  }

  // Get database connection string based on environment
  getDatabaseUrl(): string {
    const cfg = this.getConfig();
    if (cfg.databaseType === 'd1' && this.env.DB) {
      return `d1://${this.env.DB.name}`;
    } else if (cfg.databaseType === 'hyperdrive' && this.env.HYPERDRIVE) {
      return this.env.HYPERDRIVE.connectionString || this.env.DATABASE_URL || '';
    } else {
      return this.env.DATABASE_URL || 'postgresql://forge:forge_secure_password@localhost:5432/autonomousforge';
    }
  }

  // Get Redis/KV configuration
  getRedisConfig(): { type: 'redis' | 'kv'; url?: string; kv?: KVNamespace } {
    const cfg = this.getConfig();
    if (cfg.kvEnabled && this.env.SESSION_KV) {
      return { type: 'kv', kv: this.env.SESSION_KV };
    } else {
      return { type: 'redis', url: this.env.REDIS_URL || 'redis://localhost:6379' };
    }
  }

  // Get service bindings for inter-service communication
  getServiceBindings(): Record<string, Fetcher> {
    const bindings: Record<string, Fetcher> = {};
    const services = [
      'AUTH_SERVICE',
      'AGENT_REGISTRY',
      'MASTER_ORCHESTRATOR',
      'TASK_SCHEDULER',
      'MODEL_GATEWAY',
      'PROVIDER_SERVICE',
      'FILE_SERVICE',
      'MEMORY_SERVICE',
      'KNOWLEDGE_SERVICE',
      'EXECUTION_SERVICE',
      'BUILD_SERVICE',
      'TESTING_SERVICE',
      'MONITORING_SERVICE',
    ];

    for (const service of services) {
      if (this.env[service as keyof CloudflareEnv]) {
        bindings[service.toLowerCase().replace('_', '-')] = this.env[service as keyof CloudflareEnv] as Fetcher;
      }
    }

    return bindings;
  }

  // Get NVIDIA NIM configuration
  getNvidiaNimConfig(): { apiKey: string; model: string; baseUrl: string } {
    return {
      apiKey: this.env.NVIDIA_NIM_API_KEY || '',
      model: this.env.NVIDIA_NIM_MODEL || 'nemotron-3-ultra',
      baseUrl: this.env.NVIDIA_NIM_BASE_URL || 'https://integrate.api.nvidia.com/v1',
    };
  }

  // Get master API key
  getMasterApiKey(): string | undefined {
    return this.env.MASTER_API_KEY;
  }

  // Get JWT secret
  getJwtSecret(): string {
    return this.env.JWT_SECRET || 'change_this_in_production_min_32_chars';
  }
}