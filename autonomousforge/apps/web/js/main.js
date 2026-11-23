/**
 * AUTONOMOUSFORGE - Main Application Entry Point
 * Mobile-first, PWA-ready, vanilla JS with modern patterns
 */

// Configuration - will be updated by cloud config
const CONFIG = {
    API_BASE: '/api',
    WS_BASE: '/ws',
    STORAGE_KEYS: {
        AUTH_TOKEN: 'af_auth_token',
        REFRESH_TOKEN: 'af_refresh_token',
        USER_DATA: 'af_user_data',
        THEME: 'af_theme',
        SETTINGS: 'af_settings',
    },
    ROUTES: {
        LOGIN: '/login',
        SETUP: '/setup',
        DASHBOARD: '/dashboard',
        CHAT: '/chat',
        AGENTS: '/agents',
        PROJECTS: '/projects',
        SETTINGS: '/settings',
    },
};

// Update config from cloud config if available
function updateConfigFromCloud() {
    if (window.AF_CloudConfig) {
        const cloudConfig = window.AF_CloudConfig.getConfig();
        CONFIG.API_BASE = cloudConfig.apiBaseUrl;
        CONFIG.WS_BASE = cloudConfig.wsBaseUrl;
    }
}

// Initialize cloud config on load
if (typeof window !== 'undefined') {
    // Wait for cloud-config.js to load
    if (window.AF_CloudConfig) {
        updateConfigFromCloud();
    } else {
        // Listen for cloud config initialization
        window.addEventListener('af:cloudconfigready', updateConfigFromCloud);
    }
}

// State management
const state = {
    user: null,
    isAuthenticated: false,
    currentPage: null,
    theme: 'dark',
    sidebarOpen: false,
    toasts: [],
    loading: false,
};

// DOM references
const dom = {
    app: null,
    header: null,
    sidebar: null,
    main: null,
    footer: null,
    toastContainer: null,
    modalContainer: null,
};

// Utility functions
const utils = {
    // DOM manipulation
    $(selector, context = document) {
        return context.querySelector(selector);
    },
    $$(selector, context = document) {
        return Array.from(context.querySelectorAll(selector));
    },
    create(tag, attrs = {}, children = []) {
        const el = document.createElement(tag);
        Object.entries(attrs).forEach(([key, value]) => {
            if (key === 'class') el.className = value;
            else if (key === 'style') Object.assign(el.style, value);
            else if (key.startsWith('on') && typeof value === 'function') {
                el.addEventListener(key.slice(2).toLowerCase(), value);
            } else if (key === 'dataset') {
                Object.entries(value).forEach(([k, v]) => el.dataset[k] = v);
            } else {
                el.setAttribute(key, value);
            }
        });
        children.forEach(child => {
            if (typeof child === 'string') el.appendChild(document.createTextNode(child));
            else if (child instanceof Node) el.appendChild(child);
            else if (Array.isArray(child)) child.forEach(c => el.appendChild(c));
        });
        return el;
    },
    html(htmlString) {
        const template = document.createElement('template');
        template.innerHTML = htmlString.trim();
        return template.content.firstElementChild;
    },

    // Storage
    storage: {
        get(key) {
            try {
                const value = localStorage.getItem(key);
                return value ? JSON.parse(value) : null;
            } catch {
                return null;
            }
        },
        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch {
                return false;
            }
        },
        remove(key) {
            localStorage.removeItem(key);
        },
        clear() {
            localStorage.clear();
        },
    },

    // HTTP requests
    async request(url, options = {}) {
        const token = utils.storage.get(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch(`${CONFIG.API_BASE}${url}`, {
            ...options,
            headers,
            credentials: 'include',
        });

        if (response.status === 401) {
            // Token expired, try refresh
            const refreshed = await auth.refreshToken();
            if (refreshed) {
                // Retry with new token
                headers['Authorization'] = `Bearer ${utils.storage.get(CONFIG.STORAGE_KEYS.AUTH_TOKEN)}`;
                return fetch(`${CONFIG.API_BASE}${url}`, { ...options, headers, credentials: 'include' });
            } else {
                // Redirect to login
                auth.logout();
                router.navigate(CONFIG.ROUTES.LOGIN);
                throw new Error('Authentication required');
            }
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Request failed' }));
            throw new Error(error.message || `HTTP ${response.status}`);
        }

        if (response.status === 204) return null;
        return response.json();
    },

    get(url) { return utils.request(url, { method: 'GET' }); },
    post(url, data) { return utils.request(url, { method: 'POST', body: JSON.stringify(data) }); },
    put(url, data) { return utils.request(url, { method: 'PUT', body: JSON.stringify(data) }); },
    patch(url, data) { return utils.request(url, { method: 'PATCH', body: JSON.stringify(data) }); },
    delete(url) { return utils.request(url, { method: 'DELETE' }); },

    // Date formatting
    formatDate(date, options = {}) {
        const d = new Date(date);
        return d.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            ...options,
        });
    },
    formatTime(date) {
        return new Date(date).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
    },
    formatRelative(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (seconds < 60) return 'just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return utils.formatDate(date);
    },

    // Debounce
    debounce(fn, delay) {
        let timeoutId;
        return (...args) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => fn(...args), delay);
        };
    },

    // Throttle
    throttle(fn, limit) {
        let inThrottle;
        return (...args) => {
            if (!inThrottle) {
                fn(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Generate ID
    generateId() {
        return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    },

    // Escape HTML
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // Copy to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            toast.success('Copied to clipboard');
        } catch {
            toast.error('Failed to copy');
        }
    },
};

// Import components
import './components/index.js';

// Authentication module
const auth = {
    async init() {
        const token = utils.storage.get(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        const userData = utils.storage.get(CONFIG.STORAGE_KEYS.USER_DATA);
        if (token && userData) {
            state.user = userData;
            state.isAuthenticated = true;
            // Validate token
            try {
                await utils.get('/auth/me');
                return true;
            } catch {
                await this.logout();
                return false;
            }
        }
        return false;
    },
    async login(email, password, rememberMe = false) {
        const response = await utils.post('/auth/login', { email, password, remember_me: rememberMe });
        if (response.requires_2fa) {
            return { requires2fa: true, email };
        }
        utils.storage.set(CONFIG.STORAGE_KEYS.AUTH_TOKEN, response.access_token);
        utils.storage.set(CONFIG.STORAGE_KEYS.REFRESH_TOKEN, response.refresh_token);
        utils.storage.set(CONFIG.STORAGE_KEYS.USER_DATA, response.owner);
        state.user = response.owner;
        state.isAuthenticated = true;
        return { success: true };
    },
    async login2fa(email, code) {
        const response = await utils.post('/auth/login/2fa', { email, code });
        utils.storage.set(CONFIG.STORAGE_KEYS.AUTH_TOKEN, response.access_token);
        utils.storage.set(CONFIG.STORAGE_KEYS.REFRESH_TOKEN, response.refresh_token);
        utils.storage.set(CONFIG.STORAGE_KEYS.USER_DATA, response.owner);
        state.user = response.owner;
        state.isAuthenticated = true;
        return { success: true };
    },
    async logout() {
        try {
            await utils.post('/auth/logout');
        } catch {}
        utils.storage.remove(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        utils.storage.remove(CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
        utils.storage.remove(CONFIG.STORAGE_KEYS.USER_DATA);
        state.user = null;
        state.isAuthenticated = false;
    },
    async refreshToken() {
        const refreshToken = utils.storage.get(CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
        if (!refreshToken) return false;
        try {
            const response = await utils.post('/auth/refresh', { refresh_token: refreshToken });
            utils.storage.set(CONFIG.STORAGE_KEYS.AUTH_TOKEN, response.access_token);
            return true;
        } catch {
            return false;
        }
    },
    async setupOwner(data) {
        const response = await utils.post('/auth/setup', data);
        return response;
    },
    async checkSetup() {
        return utils.get('/auth/setup/status');
    },
    getUser() {
        return state.user;
    },
    isAuthenticated() {
        return state.isAuthenticated;
    },
};

// Router
const router = {
    routes: new Map(),
    currentRoute: null,
    beforeEach: null,
    afterEach: null,

    add(path, handler) {
        this.routes.set(path, handler);
    },

    navigate(path, replace = false) {
        if (this.beforeEach) this.beforeEach(path);
        const handler = this.routes.get(path);
        if (handler) {
            this.currentRoute = path;
            history[replace ? 'replaceState' : 'pushState'](null, '', path);
            handler();
            if (this.afterEach) this.afterEach(path);
        } else {
            console.warn(`Route not found: ${path}`);
            this.navigate(CONFIG.ROUTES.DASHBOARD);
        }
    },

    start() {
        window.addEventListener('popstate', () => {
            this.handleRoute(location.pathname);
        });
        this.handleRoute(location.pathname);
    },

    handleRoute(path) {
        // Match dynamic routes
        for (const [routePath, handler] of this.routes) {
            const regex = new RegExp('^' + routePath.replace(/:[^/]+/g, '([^/]+)') + '$');
            const match = path.match(regex);
            if (match) {
                const params = {};
                const paramNames = routePath.match(/:([^/]+)/g) || [];
                paramNames.forEach((name, i) => {
                    params[name.slice(1)] = match[i + 1];
                });
                this.currentRoute = path;
                handler(params);
                return;
            }
        }
        // 404
        this.navigate(CONFIG.ROUTES.DASHBOARD, true);
    },
};

// Page lifecycle
const page = {
    current: null,
    async load(pageName, params = {}) {
        // Unload current page
        if (this.current && this.current.unload) {
            await this.current.unload();
        }

        // Show loading
        ui.setLoading(true);

        try {
            // Dynamic import page module
            const module = await import(`/js/pages/${pageName}.js`);
            this.current = module.default;

            // Initialize page
            if (this.current.init) {
                await this.current.init(params);
            }

            // Render page
            if (this.current.render) {
                const content = this.current.render(params);
                dom.app.innerHTML = '';
                dom.app.appendChild(content);
            }

            // Mount page
            if (this.current.mount) {
                this.current.mount();
            }

            state.currentPage = pageName;
        } catch (error) {
            console.error(`Failed to load page: ${pageName}`, error);
            toast.error('Failed to load page');
            router.navigate(CONFIG.ROUTES.DASHBOARD);
        } finally {
            ui.setLoading(false);
        }
    },
};

// UI helpers
const ui = {
    setLoading(loading) {
        state.loading = loading;
        const loader = document.getElementById('page-loader');
        if (loader) {
            loader.style.display = loading ? 'block' : 'none';
        }
    },
    toggleSidebar() {
        state.sidebarOpen = !state.sidebarOpen;
        document.body.classList.toggle('sidebar-open', state.sidebarOpen);
    },
    closeSidebar() {
        state.sidebarOpen = false;
        document.body.classList.remove('sidebar-open');
    },
    setTheme(theme) {
        state.theme = theme;
        document.documentElement.classList.toggle('dark', theme === 'dark');
        utils.storage.set(CONFIG.STORAGE_KEYS.THEME, theme);
    },
    initTheme() {
        const saved = utils.storage.get(CONFIG.STORAGE_KEYS.THEME);
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        this.setTheme(saved || (prefersDark ? 'dark' : 'light'));
    },
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    truncate(text, length = 100) {
        if (text.length <= length) return text;
        return text.slice(0, length) + '...';
    },
    debounce: utils.debounce,
    throttle: utils.throttle,
};

// WebSocket connection
const ws = {
    socket: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    reconnectDelay: 1000,
    handlers: new Map(),

    connect() {
        if (this.socket?.readyState === WebSocket.OPEN) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}${CONFIG.WS_BASE}`;

        this.socket = new WebSocket(url);

        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.send({ type: 'auth', token: utils.storage.get(CONFIG.STORAGE_KEYS.AUTH_TOKEN) });
        };

        this.socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (e) {
                console.error('WS message parse error', e);
            }
        };

        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            this.attemptReconnect();
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error', error);
        };
    },

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            setTimeout(() => this.connect(), delay);
        }
    },

    send(data) {
        if (this.socket?.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        }
    },

    on(event, handler) {
        if (!this.handlers.has(event)) this.handlers.set(event, []);
        this.handlers.get(event).push(handler);
    },

    off(event, handler) {
        const handlers = this.handlers.get(event);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index > -1) handlers.splice(index, 1);
        }
    },

    handleMessage(message) {
        const handlers = this.handlers.get(message.type) || [];
        handlers.forEach(handler => handler(message.data));
        // Also call wildcard handlers
        const wildcards = this.handlers.get('*') || [];
        wildcards.forEach(handler => handler(message));
    },

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    },
};

// Initialize app
async function initApp() {
    // Cache DOM references
    dom.app = document.getElementById('app');

    // Initialize systems
    ui.initTheme();
    AF.Components.Toast.init();
    AF.Components.Modal.init && AF.Components.Modal.init();

    // Check authentication
    const authenticated = await auth.init();

    // Setup router
    setupRoutes();

    // Start router
    router.start();

    // Connect WebSocket if authenticated
    if (authenticated) {
        ws.connect();
    }

    // Register global event listeners
    document.addEventListener('click', (e) => {
        // Close sidebar on outside click
        if (state.sidebarOpen && !e.target.closest('.sidebar') && !e.target.closest('.sidebar-toggle')) {
            ui.closeSidebar();
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Escape closes modals/sidebar
        if (e.key === 'Escape') {
            AF.Components.Modal.closeAll();
            ui.closeSidebar();
        }
        // Cmd/Ctrl + K for command palette
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            // TODO: Open command palette
        }
    });

    console.log('AUTONOMOUSFORGE initialized');
}

// Route definitions
function setupRoutes() {
    // Public routes
    router.add(CONFIG.ROUTES.LOGIN, () => page.load('login'));
    router.add(CONFIG.ROUTES.SETUP, () => page.load('setup'));

    // Protected routes
    const protectedRoutes = [
        CONFIG.ROUTES.DASHBOARD,
        CONFIG.ROUTES.CHAT,
        CONFIG.ROUTES.AGENTS,
        CONFIG.ROUTES.PROJECTS,
        CONFIG.ROUTES.SETTINGS,
    ];

    protectedRoutes.forEach(route => {
        router.add(route, () => {
            if (!auth.isAuthenticated()) {
                router.navigate(CONFIG.ROUTES.LOGIN);
                return;
            }
            const pageName = route.slice(1).replace('/', '-') || 'dashboard';
            page.load(pageName);
        });
    });

    // Default redirect
    router.beforeEach = (path) => {
        if (path === '/' || path === '') {
            router.navigate(auth.isAuthenticated() ? CONFIG.ROUTES.DASHBOARD : CONFIG.ROUTES.LOGIN, true);
        }
    };
}

// Export for use in pages
window.AF = {
    CONFIG,
    state,
    utils,
    auth,
    router,
    page,
    ui,
    toast: AF.Components.Toast,
    modal: AF.Components.Modal,
    ws,
    dom,
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Service Worker registration handled in HTML