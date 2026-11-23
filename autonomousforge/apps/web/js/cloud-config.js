/**
 * AUTONOMOUSFORGE - Cloud Configuration (Frontend)
 * Auto-detects deployment environment and configures API endpoints, visual themes, and features
 */

(function() {
    'use strict';

    // Cloud Configuration Module
    const CloudConfig = (function() {
        let config = null;
        let initialized = false;

        // Default configuration
        const defaults = {
            // Environment
            isCloudflare: false,
            isCloudflarePages: false,
            isCloudflareWorker: false,
            isLocal: true,

            // Database
            databaseType: 'postgresql', // postgresql, d1, hyperdrive
            d1DatabaseId: null,
            hyperdriveEnabled: false,

            // Storage
            kvEnabled: false,
            r2Enabled: false,

            // AI
            workersAIEnabled: false,

            // Visual theme
            themeMode: 'purple', // auto, dark, light, purple, cloudflare
            primaryColor: '#7c3aed',
            accentColor: '#a855f7',
            backgroundColor: '#0f172a',
            surfaceColor: '#1e293b',

            // API Endpoints
            apiBaseUrl: '/api',
            wsBaseUrl: '/ws',
            frontendUrl: '',
            apiDomain: '',

            // Feature flags
            enableBackgroundSync: true,
            enablePushNotifications: true,
            enableOfflineSupport: true,
            enableServiceWorker: true,
        };

        function detectEnvironment() {
            const env = { ...defaults };

            // Detect Cloudflare Pages
            if (typeof window !== 'undefined') {
                const hostname = window.location.hostname;

                // Cloudflare Pages deployment
                if (hostname.endsWith('.pages.dev') ||
                    hostname.includes('cloudflare') ||
                    window.CF_PAGES === true) {
                    env.isCloudflare = true;
                    env.isCloudflarePages = true;
                    env.isLocal = false;
                }

                // Cloudflare Workers (check for Worker-specific headers or env)
                if (window.CF_WORKER === true) {
                    env.isCloudflare = true;
                    env.isCloudflareWorker = true;
                    env.isLocal = false;
                }

                // Check for custom domain on Cloudflare
                if (env.isCloudflarePages && !hostname.endsWith('.pages.dev')) {
                    env.apiDomain = hostname.replace(/^[^.]+\./, 'api.');
                }
            }

            // Check for environment variables (injected at build time)
            if (typeof __CLOUDFLARE_DEPLOY__ !== 'undefined') {
                env.isCloudflare = true;
                env.isCloudflarePages = __CLOUDFLARE_PAGES__ || false;
                env.isCloudflareWorker = __CLOUDFLARE_WORKER__ || false;
                env.isLocal = false;
            }

            // Check for D1 database
            if (typeof __D1_DATABASE_ID__ !== 'undefined') {
                env.databaseType = 'd1';
                env.d1DatabaseId = __D1_DATABASE_ID__;
            }

            // Check for Hyperdrive
            if (typeof __HYPERDRIVE_ENABLED__ !== 'undefined') {
                env.databaseType = 'hyperdrive';
                env.hyperdriveEnabled = true;
            }

            // Check for KV
            if (typeof __KV_ENABLED__ !== 'undefined') {
                env.kvEnabled = true;
            }

            // Check for R2
            if (typeof __R2_ENABLED__ !== 'undefined') {
                env.r2Enabled = true;
            }

            // Check for Workers AI
            if (typeof __WORKERS_AI_ENABLED__ !== 'undefined') {
                env.workersAIEnabled = true;
            }

            // Override from meta tags (for static deployments)
            if (typeof document !== 'undefined') {
                const metaTheme = document.querySelector('meta[name="af-theme-mode"]');
                if (metaTheme) env.themeMode = metaTheme.getAttribute('content');

                const metaPrimary = document.querySelector('meta[name="af-primary-color"]');
                if (metaPrimary) env.primaryColor = metaPrimary.getAttribute('content');

                const metaApiDomain = document.querySelector('meta[name="af-api-domain"]');
                if (metaApiDomain) env.apiDomain = metaApiDomain.getAttribute('content');

                const metaApiBase = document.querySelector('meta[name="af-api-base"]');
                if (metaApiBase) env.apiBaseUrl = metaApiBase.getAttribute('content');

                const metaWsBase = document.querySelector('meta[name="af-ws-base"]');
                if (metaWsBase) env.wsBaseUrl = metaWsBase.getAttribute('content');
            }

            return env;
        }

        function configureVisualTheme(env) {
            // Cloudflare theme
            if (env.isCloudflare && env.themeMode === 'cloudflare') {
                env.primaryColor = '#f38020'; // Cloudflare orange
                env.accentColor = '#ff9500';
                env.backgroundColor = '#0f172a';
                env.surfaceColor = '#1e293b';
            }
            // Purple theme (default)
            else if (env.themeMode === 'purple' || env.themeMode === 'auto') {
                env.primaryColor = '#7c3aed';
                env.accentColor = '#a855f7';
                env.backgroundColor = '#0f172a';
                env.surfaceColor = '#1e293b';
            }
            // Dark theme
            else if (env.themeMode === 'dark') {
                env.primaryColor = '#6366f1';
                env.accentColor = '#818cf8';
                env.backgroundColor = '#020617';
                env.surfaceColor = '#0f172a';
            }
            // Light theme
            else if (env.themeMode === 'light') {
                env.primaryColor = '#4f46e5';
                env.accentColor = '#6366f1';
                env.backgroundColor = '#ffffff';
                env.surfaceColor = '#f8fafc';
            }

            // Apply CSS custom properties
            if (typeof document !== 'undefined') {
                const root = document.documentElement;
                root.style.setProperty('--af-primary', env.primaryColor);
                root.style.setProperty('--af-accent', env.accentColor);
                root.style.setProperty('--af-bg', env.backgroundColor);
                root.style.setProperty('--af-surface', env.surfaceColor);
                root.style.setProperty('--af-primary-hover', adjustColor(env.primaryColor, -20));
                root.style.setProperty('--af-primary-light', adjustColor(env.primaryColor, 40));
                root.style.setProperty('--af-accent-hover', adjustColor(env.accentColor, -20));

                // Add theme class
                root.classList.remove('theme-purple', 'theme-cloudflare', 'theme-dark', 'theme-light');
                root.classList.add(`theme-${env.themeMode}`);
            }
        }

        function adjustColor(color, amount) {
            // Simple color brightness adjustment
            const hex = color.replace('#', '');
            const r = Math.max(0, Math.min(255, parseInt(hex.slice(0, 2), 16) + amount));
            const g = Math.max(0, Math.min(255, parseInt(hex.slice(2, 4), 16) + amount));
            const b = Math.max(0, Math.min(255, parseInt(hex.slice(4, 6), 16) + amount));
            return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
        }

        function configureEndpoints(env) {
            if (env.isCloudflarePages) {
                // Frontend on Cloudflare Pages
                env.frontendUrl = window.location.origin;
                if (env.apiDomain) {
                    env.apiBaseUrl = `https://${env.apiDomain}/api`;
                    env.wsBaseUrl = `wss://${env.apiDomain}/ws`;
                } else {
                    // Same domain, different path
                    env.apiBaseUrl = `${window.location.origin}/api`;
                    env.wsBaseUrl = `${window.location.origin.replace('https:', 'wss:')}/ws`;
                }
            } else if (env.isCloudflareWorker) {
                // API on Cloudflare Workers
                if (env.apiDomain) {
                    env.apiBaseUrl = `https://${env.apiDomain}/api`;
                    env.wsBaseUrl = `wss://${env.apiDomain}/ws`;
                }
            } else {
                // Local development
                env.frontendUrl = window.location.origin;
                env.apiBaseUrl = '/api';
                env.wsBaseUrl = '/ws';
            }
        }

        function initialize() {
            if (initialized) return config;

            const env = detectEnvironment();
            configureVisualTheme(env);
            configureEndpoints(env);

            config = env;
            initialized = true;

            // Expose globally
            if (typeof window !== 'undefined') {
                window.AF_CLOUD_CONFIG = config;
            }

            console.log('[CloudConfig] Initialized:', {
                environment: config.isCloudflare ? 'cloudflare' : 'local',
                deployment: config.isCloudflarePages ? 'pages' : (config.isCloudflareWorker ? 'worker' : 'local'),
                theme: config.themeMode,
                apiBase: config.apiBaseUrl,
                wsBase: config.wsBaseUrl,
                database: config.databaseType,
            });

            return config;
        }

        function getConfig() {
            if (!initialized) initialize();
            return config;
        }

        function getApiBaseUrl() {
            return getConfig().apiBaseUrl;
        }

        function getWsBaseUrl() {
            return getConfig().wsBaseUrl;
        }

        function getVisualTheme() {
            const cfg = getConfig();
            return {
                themeMode: cfg.themeMode,
                primaryColor: cfg.primaryColor,
                accentColor: cfg.accentColor,
                backgroundColor: cfg.backgroundColor,
                surfaceColor: cfg.surfaceColor,
                isCloudflare: cfg.isCloudflare,
            };
        }

        function isCloudflare() {
            return getConfig().isCloudflare;
        }

        function isLocal() {
            return getConfig().isLocal;
        }

        function getDatabaseType() {
            return getConfig().databaseType;
        }

        function getFeatureFlags() {
            const cfg = getConfig();
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

        // Theme switching
        function setTheme(themeMode) {
            const cfg = getConfig();
            cfg.themeMode = themeMode;
            configureVisualTheme(cfg);

            // Persist to localStorage
            if (typeof localStorage !== 'undefined') {
                localStorage.setItem('af_theme_mode', themeMode);
            }

            // Dispatch theme change event
            if (typeof window !== 'undefined') {
                window.dispatchEvent(new CustomEvent('af:themechange', { detail: getVisualTheme() }));
            }
        }

        function toggleTheme() {
            const cfg = getConfig();
            const themes = ['purple', 'dark', 'light'];
            const currentIndex = themes.indexOf(cfg.themeMode);
            const nextIndex = (currentIndex + 1) % themes.length;
            setTheme(themes[nextIndex]);
        }

        // Initialize immediately
        initialize();

        // Public API
        return {
            initialize,
            getConfig,
            getApiBaseUrl,
            getWsBaseUrl,
            getVisualTheme,
            getFeatureFlags,
            isCloudflare,
            isLocal,
            getDatabaseType,
            setTheme,
            toggleTheme,
        };
    })();

    // Export for module systems
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = CloudConfig;
    }

    // Global export
    if (typeof window !== 'undefined') {
        window.AF_CloudConfig = CloudConfig;
    }
})();