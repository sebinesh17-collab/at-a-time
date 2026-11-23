/**
 * Dashboard Page - Main Overview
 */
export default {
    async init() {
        if (!AF.auth.isAuthenticated()) {
            AF.router.navigate(AF.CONFIG.ROUTES.LOGIN, true);
            return;
        }
        await this.loadData();
    },

    async loadData() {
        try {
            const [stats, recentActivity, agentStatus] = await Promise.all([
                AF.utils.get('/monitoring/stats'),
                AF.utils.get('/monitoring/recent-activity?limit=10'),
                AF.utils.get('/agents/status/summary'),
            ]).catch(() => [{}, [], {}]);

            this.stats = stats;
            this.recentActivity = recentActivity;
            this.agentStatus = agentStatus;
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    },

    render() {
        const user = AF.auth.getUser();
        const stats = this.stats || {};
        const agentStatus = this.agentStatus || {};

        return AF.utils.create('div', { class: 'min-h-screen', id: 'dashboard-page' }, [
            // Mobile Header
            AF.utils.create('header', { class: 'fixed top-0 left-0 right-0 h-14 bg-forge-950/95 backdrop-blur-sm border-b border-forge-800 z-40 flex items-center px-4 safe-top', role: 'banner' }, [
                AF.utils.create('button', {
                    class: 'btn btn-ghost btn-icon -ml-2 lg:hidden sidebar-toggle',
                    'aria-label': 'Open menu',
                    onclick: () => AF.ui.toggleSidebar(),
                }, [
                    AF.utils.create('svg', { class: 'w-6 h-6', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                        AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 6h16M4 12h16M4 18h16' }),
                    ]),
                ]),
                AF.utils.create('div', { class: 'flex-1 text-center' }, [
                    AF.utils.create('h1', { class: 'text-lg font-semibold text-forge-50' }, 'Dashboard'),
                ]),
                AF.utils.create('div', { class: 'w-10 lg:hidden' }), // Spacer
            ]),

            // Sidebar (Mobile Drawer / Desktop Fixed)
            AF.utils.create('aside', { class: 'fixed inset-y-0 left-0 z-50 w-64 bg-forge-950 border-r border-forge-800 transform -translate-x-full lg:translate-x-0 transition-transform duration-300 ease-out sidebar safe-top', role: 'navigation', 'aria-label': 'Main navigation' }, [
                AF.utils.create('div', { class: 'flex flex-col h-full' }, [
                    // Brand
                    AF.utils.create('div', { class: 'p-4 border-b border-forge-800' }, [
                        AF.utils.create('a', { href: '#', class: 'flex items-center gap-3', onclick: (e) => { e.preventDefault(); AF.router.navigate(AF.CONFIG.ROUTES.DASHBOARD); } }, [
                            AF.utils.create('div', { class: 'w-10 h-10 rounded-xl bg-forge-800 border border-forge-700 flex items-center justify-center' }, [
                                AF.utils.create('svg', { class: 'w-6 h-6 text-accent-500', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                                    AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M13 10V3L4 14h7v7l9-11h-7z' }),
                                ]),
                            ]),
                            AF.utils.create('div', {}, [
                                AF.utils.create('span', { class: 'font-bold text-forge-50' }, 'AUTONOMOUSFORGE'),
                                AF.utils.create('span', { class: 'block text-xs text-forge-500' }, 'Private OS'),
                            ]),
                        ]),
                    ]),

                    // Navigation
                    AF.utils.create('nav', { class: 'flex-1 p-3 space-y-1 overflow-y-auto' }, [
                        ...this.navItems.map(item => AF.utils.create('a', {
                            href: '#',
                            class: `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${item.active ? 'bg-accent-500/10 text-accent-400' : 'text-forge-400 hover:text-forge-100 hover:bg-forge-800'}`,
                            'data-page': item.page,
                            onclick: (e) => {
                                e.preventDefault();
                                AF.router.navigate(item.route);
                                AF.ui.closeSidebar();
                            },
                        }, [
                            AF.utils.create('span', { class: 'w-5 h-5 flex items-center justify-center' }, item.icon),
                            item.label,
                            item.badge && AF.utils.create('span', { class: 'ml-auto px-2 py-0.5 text-xs font-medium rounded-full bg-forge-700 text-forge-300' }, item.badge),
                        ])),
                    ]),

                    // User section
                    AF.utils.create('div', { class: 'p-3 border-t border-forge-800' }, [
                        AF.utils.create('div', { class: 'flex items-center gap-3 mb-3' }, [
                            AF.utils.create('div', { class: 'w-10 h-10 rounded-xl bg-forge-800 border border-forge-700 flex items-center justify-center text-forge-300 font-semibold' }, user?.display_name?.[0]?.toUpperCase() || 'O'),
                            AF.utils.create('div', { class: 'flex-1 min-w-0' }, [
                                AF.utils.create('p', { class: 'font-medium text-forge-100 truncate' }, user?.display_name || 'Owner'),
                                AF.utils.create('p', { class: 'text-xs text-forge-500 truncate' }, user?.email || ''),
                            ]),
                        ]),
                        AF.utils.create('div', { class: 'flex gap-2' }, [
                            AF.utils.create('a', { href: '#', class: 'btn btn-ghost btn-sm flex-1', 'data-page': 'settings', onclick: (e) => { e.preventDefault(); AF.router.navigate(AF.CONFIG.ROUTES.SETTINGS); AF.ui.closeSidebar(); } }, [
                                AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' }),]),
                                'Settings',
                            ]),
                            AF.utils.create('button', { class: 'btn btn-ghost btn-sm', onclick: () => AF.auth.logout().then(() => AF.router.navigate(AF.CONFIG.ROUTES.LOGIN)) }, [
                                AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1' }),]),
                            ]),
                        ]),
                    ]),
                ]),
            ]),

            // Sidebar overlay (mobile)
            AF.utils.create('div', { class: 'fixed inset-0 z-40 bg-black/50 hidden lg:hidden sidebar-overlay', onclick: () => AF.ui.closeSidebar(), 'aria-hidden': 'true' }),

            // Main Content
            AF.utils.create('main', { class: 'flex-1 pt-14 lg:pt-0 lg:ml-64 min-h-screen', role: 'main' }, [
                AF.utils.create('div', { class: 'p-4 lg:p-6 space-y-6' }, [
                    // Welcome Header
                    AF.utils.create('div', { class: 'flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4' }, [
                        AF.utils.create('div', {}, [
                            AF.utils.create('h2', { class: 'text-2xl font-bold text-forge-50' }, `Welcome back, ${user?.display_name?.split(' ')[0] || 'Owner'}`),
                            AF.utils.create('p', { class: 'text-forge-400 mt-1' }, 'Your private autonomous engineering OS'),
                        ]),
                        AF.utils.create('div', { class: 'flex gap-2' }, [
                            AF.utils.create('button', { class: 'btn btn-primary', onclick: () => AF.router.navigate(AF.CONFIG.ROUTES.CHAT) }, [
                                AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' }),]),
                                ' New Chat',
                            ]),
                            AF.utils.create('button', { class: 'btn btn-secondary', onclick: () => AF.router.navigate(AF.CONFIG.ROUTES.PROJECTS) }, [
                                AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 6v6m0 0v6m0-6h6m-6 0H6' }),]),
                                ' New Project',
                            ]),
                        ]),
                    ]),

                    // Stats Grid
                    AF.utils.create('div', { class: 'grid grid-cols-2 lg:grid-cols-4 gap-4', role: 'region', 'aria-label': 'System statistics' }, [
                        this.renderStatCard('Total Agents', stats.total_agents || '16,111', 'accent', [
                            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' }),
                        ]),
                        this.renderStatCard('Active Tasks', stats.active_tasks || '0', 'info', [
                            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4' }),
                        ]),
                        this.renderStatCard('Models Available', stats.models_available || '12', 'warning', [
                            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4' }),
                        ]),
                        this.renderStatCard('API Keys', stats.api_keys || '0', 'neutral', [
                            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z' }),
                        ]),
                    ]),

                    // Agent Status Overview
                    AF.utils.create('div', { class: 'grid lg:grid-cols-2 gap-4' }, [
                        AF.utils.create('div', { class: 'card' }, [
                            AF.utils.create('div', { class: 'card-header flex items-center justify-between' }, [
                                AF.utils.create('h3', { class: 'font-semibold' }, 'Agent Hierarchy Status'),
                                AF.utils.create('a', { href: '#', class: 'text-sm text-accent-500 hover:underline', onclick: (e) => { e.preventDefault(); AF.router.navigate(AF.CONFIG.ROUTES.AGENTS); } }, 'View All'),
                            ]),
                            AF.utils.create('div', { class: 'card-body space-y-3' }, [
                                ...this.renderAgentLevel('Master', 1, agentStatus.master || { active: 1, total: 1 }),
                                ...this.renderAgentLevel('Principals', 10, agentStatus.principals || { active: 8, total: 10 }),
                                ...this.renderAgentLevel('Heads', 100, agentStatus.heads || { active: 45, total: 100 }),
                                ...this.renderAgentLevel('Team Leaders', 1,000, agentStatus.team_leaders || { active: 320, total: 1000 }),
                                ...this.renderAgentLevel('Workers', 15,000, agentStatus.workers || { active: 1200, total: 15000 }),
                            ]),
                        ]),

                        // Recent Activity
                        AF.utils.create('div', { class: 'card' }, [
                            AF.utils.create('div', { class: 'card-header flex items-center justify-between' }, [
                                AF.utils.create('h3', { class: 'font-semibold' }, 'Recent Activity'),
                                AF.utils.create('a', { href: '#', class: 'text-sm text-accent-500 hover:underline', onclick: (e) => { e.preventDefault(); AF.router.navigate(AF.CONFIG.ROUTES.AGENTS); } }, 'View All'),
                            ]),
                            AF.utils.create('div', { class: 'card-body' }, [
                                this.recentActivity.length > 0 ? AF.utils.create('div', { class: 'space-y-3' }, this.recentActivity.map(activity => AF.utils.create('div', { class: 'flex items-start gap-3 p-3 bg-forge-900/50 rounded-lg' }, [
                                    AF.utils.create('div', { class: `w-2 h-2 rounded-full mt-2 flex-shrink-0 ${this.getActivityColor(activity.type)}` }),
                                    AF.utils.create('div', { class: 'flex-1 min-w-0' }, [
                                        AF.utils.create('p', { class: 'text-sm text-forge-300' }, activity.message),
                                        AF.utils.create('p', { class: 'text-xs text-forge-500 mt-0.5' }, AF.utils.formatRelative(activity.timestamp)),
                                    ]),
                                ])) : AF.utils.create('div', { class: 'text-center py-8 text-forge-500' }, [
                                    AF.utils.create('svg', { class: 'w-12 h-12 mx-auto mb-3 text-forge-700', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '1.5', d: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' })]),
                                    AF.utils.create('p', { class: 'font-medium' }, 'No recent activity'),
                                    AF.utils.create('p', { class: 'text-sm mt-1' }, 'Start a chat or create a project to begin'),
                                ]),
                            ]),
                        ]),
                    ]),

                    // Quick Actions
                    AF.utils.create('div', { class: 'card' }, [
                        AF.utils.create('div', { class: 'card-header' }, [
                            AF.utils.create('h3', { class: 'font-semibold' }, 'Quick Actions'),
                        ]),
                        AF.utils.create('div', { class: 'card-body' }, [
                            AF.utils.create('div', { class: 'grid grid-cols-2 lg:grid-cols-4 gap-3' }, this.quickActions.map(action => AF.utils.create('button', {
                                class: 'btn btn-secondary h-24 flex-col gap-2 p-4 hover:bg-forge-800 border-forge-700',
                                onclick: () => action.onClick(),
                            }, [
                                AF.utils.create('div', { class: 'w-10 h-10 rounded-lg bg-forge-800 border border-forge-700 flex items-center justify-center text-lg' }, action.icon),
                                AF.utils.create('span', { class: 'font-medium text-sm text-center' }, action.label),
                            ])),
                        ]),
                    ]),
                ]),
            ]),
        ]);
    },

    renderStatCard(label, value, color, iconPath) {
        const colors = {
            accent: 'bg-accent-500/10 border-accent-500/20 text-accent-400',
            info: 'bg-info-500/10 border-info-500/20 text-info-400',
            warning: 'bg-warning-500/10 border-warning-500/20 text-warning-400',
            neutral: 'bg-forge-800 border-forge-700 text-forge-300',
        };

        return AF.utils.create('div', { class: `card p-4 border ${colors[color]}` }, [
            AF.utils.create('div', { class: 'flex items-start justify-between' }, [
                AF.utils.create('div', {}, [
                    AF.utils.create('p', { class: 'text-sm font-medium text-forge-400' }, label),
                    AF.utils.create('p', { class: 'text-2xl font-bold mt-1' }, value),
                ]),
                AF.utils.create('div', { class: 'w-10 h-10 rounded-lg flex items-center justify-center' }, [
                    AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, iconPath),
                ]),
            ]),
        ]);
    },

    renderAgentLevel(name, total, status) {
        const active = status.active || 0;
        const percentage = total > 0 ? Math.round((active / total) * 100) : 0;

        return AF.utils.create('div', { class: 'flex items-center gap-3' }, [
            AF.utils.create('div', { class: 'w-8 h-8 rounded-lg bg-forge-800 border border-forge-700 flex items-center justify-center flex-shrink-0' }, [
                AF.utils.create('span', { class: 'text-xs font-mono text-forge-400' }, this.getLevelIcon(name)),
            ]),
            AF.utils.create('div', { class: 'flex-1 min-w-0' }, [
                AF.utils.create('div', { class: 'flex justify-between text-sm' }, [
                    AF.utils.create('span', { class: 'font-medium text-forge-300' }, name),
                    AF.utils.create('span', { class: 'text-forge-500' }, `${active}/${total}`),
                ]),
                AF.utils.create('div', { class: 'h-1.5 bg-forge-800 rounded-full mt-1 overflow-hidden' }, [
                    AF.utils.create('div', {
                        class: 'h-full bg-accent-500 rounded-full transition-all duration-500',
                        style: `width: ${percentage}%`,
                    }),
                ]),
            ]),
        ]);
    },

    getLevelIcon(name) {
        const icons = { 'Master': 'M', 'Principals': 'P', 'Heads': 'H', 'Team Leaders': 'T', 'Workers': 'W' };
        return icons[name] || '?';
    },

    getActivityColor(type) {
        const colors = {
            task: 'bg-info-500',
            agent: 'bg-accent-500',
            model: 'bg-warning-500',
            error: 'bg-danger-500',
            deploy: 'bg-purple-500',
        };
        return colors[type] || 'bg-forge-500';
    },

    quickActions = [
        { label: 'New Chat', icon: '💬', onClick: () => AF.router.navigate(AF.CONFIG.ROUTES.CHAT) },
        { label: 'New Project', icon: '📁', onClick: () => AF.router.navigate(AF.CONFIG.ROUTES.PROJECTS) },
        { label: 'Agent Center', icon: '🤖', onClick: () => AF.router.navigate(AF.CONFIG.ROUTES.AGENTS) },
        { label: 'Upload Files', icon: '📤', onClick: () => AF.router.navigate(AF.CONFIG.ROUTES.CHAT + '?mode=files') },
    ],

    navItems = [
        { page: 'dashboard', label: 'Dashboard', route: AF.CONFIG.ROUTES.DASHBOARD, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' })]), active: true },
        { page: 'chat', label: 'AI Chat', route: AF.CONFIG.ROUTES.CHAT, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' })]) },
        { page: 'agents', label: 'Agent Center', route: AF.CONFIG.ROUTES.AGENTS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' })]) },
        { page: 'projects', label: 'Projects', route: AF.CONFIG.ROUTES.PROJECTS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z' })]) },
        { page: 'settings', label: 'Settings', route: AF.CONFIG.ROUTES.SETTINGS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' })]) },
    ],

    mount() {
        // Update active nav item
        this.updateActiveNav();

        // Listen for route changes
        window.addEventListener('popstate', () => this.updateActiveNav());
    },

    updateActiveNav() {
        const currentPath = location.pathname;
        document.querySelectorAll('[data-page]').forEach(el => {
            const page = el.dataset.page;
            const isActive = currentPath === AF.CONFIG.ROUTES[page.toUpperCase()] ||
                (page === 'dashboard' && (currentPath === '/' || currentPath === ''));
            el.classList.toggle('bg-accent-500/10', isActive);
            el.classList.toggle('text-accent-400', isActive);
            el.classList.toggle('text-forge-400', !isActive);
            el.classList.toggle('hover:text-forge-100', !isActive);
            el.classList.toggle('hover:bg-forge-800', !isActive);
        });
    },

    async unload() {
        // Cleanup if needed
    },
};