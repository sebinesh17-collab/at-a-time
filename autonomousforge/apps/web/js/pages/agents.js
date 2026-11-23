/**
 * Agents Page - Agent Hierarchy Management
 */
export default {
    agents: [],
    selectedLevel: 'all',
    searchQuery: '',
    hierarchy: null,

    async init() {
        if (!AF.auth.isAuthenticated()) {
            AF.router.navigate(AF.CONFIG.ROUTES.LOGIN, true);
            return;
        }
        await this.loadAgents();
        await this.loadHierarchy();
    },

    async loadAgents() {
        try {
            const response = await AF.utils.get('/agents?limit=100');
            this.agents = response.agents || [];
        } catch (error) {
            console.error('Failed to load agents:', error);
            this.agents = [];
        }
    },

    async loadHierarchy() {
        try {
            const response = await AF.utils.get('/agents/hierarchy');
            this.hierarchy = response;
        } catch (error) {
            console.error('Failed to load hierarchy:', error);
            this.hierarchy = {
                master: { active: 1, total: 1 },
                principals: { active: 8, total: 10 },
                heads: { active: 45, total: 100 },
                team_leaders: { active: 320, total: 1000 },
                workers: { active: 1200, total: 15000 },
            };
        }
    },

    getFilteredAgents() {
        return this.agents.filter(agent => {
            const matchesLevel = this.selectedLevel === 'all' || agent.level === this.selectedLevel;
            const matchesSearch = this.searchQuery === '' ||
                agent.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
                agent.id.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
                agent.department?.toLowerCase().includes(this.searchQuery.toLowerCase());
            return matchesLevel && matchesSearch;
        });
    },

    render() {
        const filtered = this.getFilteredAgents();

        return AF.utils.create('div', { class: 'min-h-screen', id: 'agents-page' }, [
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
                    AF.utils.create('h1', { class: 'text-lg font-semibold text-forge-50' }, 'Agent Center'),
                ]),
                AF.utils.create('div', { class: 'w-10 lg:hidden' }),
            ]),

            // Sidebar
            AF.utils.create('aside', { class: 'fixed inset-y-0 left-0 z-50 w-64 bg-forge-950 border-r border-forge-800 transform -translate-x-full lg:translate-x-0 transition-transform duration-300 ease-out sidebar safe-top', role: 'navigation' }, [
                AF.utils.create('div', { class: 'flex flex-col h-full' }, [
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
                        ])),
                    ]),
                ]),
            ]),

            // Sidebar overlay
            AF.utils.create('div', { class: 'fixed inset-0 z-40 bg-black/50 hidden lg:hidden sidebar-overlay', onclick: () => AF.ui.closeSidebar(), 'aria-hidden': 'true' }),

            // Main Content
            AF.utils.create('main', { class: 'flex-1 pt-14 lg:pt-0 lg:ml-64 min-h-screen', role: 'main' }, [
                AF.utils.create('div', { class: 'p-4 lg:p-6 space-y-6' }, [
                    // Header
                    AF.utils.create('div', { class: 'flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4' }, [
                        AF.utils.create('div', {}, [
                            AF.utils.create('h2', { class: 'text-2xl font-bold text-forge-50' }, 'Agent Hierarchy'),
                            AF.utils.create('p', { class: 'text-forge-400 mt-1' }, 'Manage and monitor 16,111 autonomous agents'),
                        ]),
                        AF.utils.create('button', { class: 'btn btn-primary', onclick: () => this.openCreateAgentModal() }, [
                            AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 4v16m8-8H4' })]),
                            ' Add Agent',
                        ]),
                    ]),

                    // Hierarchy Overview
                    AF.utils.create('div', { class: 'card' }, [
                        AF.utils.create('div', { class: 'card-header' }, [
                            AF.utils.create('h3', { class: 'font-semibold' }, 'Hierarchy Overview'),
                        ]),
                        AF.utils.create('div', { class: 'card-body' }, [
                            AF.utils.create('div', { class: 'space-y-3' }, [
                                ...this.renderHierarchyLevel('Master', 'M', 1, 1, this.hierarchy?.master || { active: 1, total: 1 }, 'accent'),
                                ...this.renderHierarchyLevel('Principals', 'P', 10, 2, this.hierarchy?.principals || { active: 8, total: 10 }, 'info'),
                                ...this.renderHierarchyLevel('Heads', 'H', 100, 3, this.hierarchy?.heads || { active: 45, total: 100 }, 'warning'),
                                ...this.renderHierarchyLevel('Team Leaders', 'TL', 1000, 4, this.hierarchy?.team_leaders || { active: 320, total: 1000 }, 'neutral'),
                                ...this.renderHierarchyLevel('Workers', 'W', 15000, 5, this.hierarchy?.workers || { active: 1200, total: 15000 }, 'secondary'),
                            ]),
                        ]),
                    ]),

                    // Agent List
                    AF.utils.create('div', { class: 'card' }, [
                        AF.utils.create('div', { class: 'card-header flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4' }, [
                            AF.utils.create('h3', { class: 'font-semibold' }, 'Agent Registry'),
                            AF.utils.create('div', { class: 'flex flex-col sm:flex-row gap-3 w-full sm:w-auto' }, [
                                AF.utils.create('div', { class: 'relative flex-1' }, [
                                    AF.utils.create('svg', { class: 'absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-forge-500', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' })]),
                                    AF.utils.create('input', {
                                        type: 'search',
                                        class: 'w-full bg-forge-800 border border-forge-700 rounded-lg pl-10 pr-4 py-2 text-forge-100 placeholder-forge-500 focus:outline-none focus:ring-2 focus:ring-accent-500',
                                        placeholder: 'Search agents...',
                                        oninput: (e) => { this.searchQuery = e.target.value; this.renderAgentList(); },
                                    }),
                                ]),
                                AF.utils.create('select', {
                                    class: 'bg-forge-800 border border-forge-700 rounded-lg px-4 py-2 text-sm text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500',
                                    onchange: (e) => { this.selectedLevel = e.target.value; this.renderAgentList(); },
                                }, [
                                    AF.utils.create('option', { value: 'all' }, 'All Levels'),
                                    AF.utils.create('option', { value: 'master' }, 'Master'),
                                    AF.utils.create('option', { value: 'principal' }, 'Principals'),
                                    AF.utils.create('option', { value: 'head' }, 'Heads'),
                                    AF.utils.create('option', { value: 'team_leader' }, 'Team Leaders'),
                                    AF.utils.create('option', { value: 'worker' }, 'Workers'),
                                ]),
                            ]),
                        ]),
                        AF.utils.create('div', { class: 'card-body' }, [
                            AF.utils.create('div', { id: 'agents-list', class: 'space-y-2' }, [
                                ...filtered.map(agent => this.renderAgentRow(agent)),
                            ]),
                        ]),
                    ]),
                ]),
            ]),
        ]);
    },

    renderHierarchyLevel(name, icon, total, depth, status, color) {
        const active = status.active || 0;
        const percentage = total > 0 ? Math.round((active / total) * 100) : 0;
        const colors = {
            accent: 'bg-accent-500/10 border-accent-500/20 text-accent-400',
            info: 'bg-info-500/10 border-info-500/20 text-info-400',
            warning: 'bg-warning-500/10 border-warning-500/20 text-warning-400',
            neutral: 'bg-forge-800 border-forge-700 text-forge-300',
            secondary: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
        };
        const barColors = {
            accent: 'bg-accent-500',
            info: 'bg-info-500',
            warning: 'bg-warning-500',
            neutral: 'bg-forge-500',
            secondary: 'bg-purple-500',
        };

        return AF.utils.create('div', { class: 'flex items-center gap-4' }, [
            AF.utils.create('div', { class: `w-10 h-10 rounded-xl border flex items-center justify-center flex-shrink-0 ${colors[color]}` }, [
                AF.utils.create('span', { class: 'text-xs font-mono font-bold' }, icon),
            ]),
            AF.utils.create('div', { class: 'flex-1 min-w-0' }, [
                AF.utils.create('div', { class: 'flex items-center justify-between' }, [
                    AF.utils.create('div', { class: 'flex items-center gap-2' }, [
                        AF.utils.create('span', { class: 'font-medium text-forge-300' }, name),
                        AF.utils.create('span', { class: `text-xs px-2 py-0.5 rounded-full ${colors[color]}` }, `Level ${depth}`),
                    ]),
                    AF.utils.create('span', { class: 'text-sm text-forge-500 font-mono' }, `${active.toLocaleString()} / ${total.toLocaleString()}`),
                ]),
                AF.utils.create('div', { class: 'h-2 bg-forge-800 rounded-full mt-1.5 overflow-hidden' }, [
                    AF.utils.create('div', {
                        class: `h-full ${barColors[color]} rounded-full transition-all duration-500`,
                        style: `width: ${percentage}%`,
                    }),
                ]),
            ]),
        ]);
    },

    renderAgentList() {
        const filtered = this.getFilteredAgents();
        const container = document.getElementById('agents-list');
        if (!container) return;

        container.innerHTML = '';
        filtered.forEach(agent => {
            container.appendChild(this.renderAgentRow(agent));
        });
    },

    renderAgentRow(agent) {
        const statusColors = {
            active: 'bg-accent-500',
            idle: 'bg-warning-500',
            busy: 'bg-info-500',
            error: 'bg-danger-500',
            offline: 'bg-forge-500',
        };
        const statusLabels = {
            active: 'Active',
            idle: 'Idle',
            busy: 'Busy',
            error: 'Error',
            offline: 'Offline',
        };

        const levelLabels = {
            master: 'Master',
            principal: 'Principal',
            head: 'Head',
            team_leader: 'Team Leader',
            worker: 'Worker',
        };

        return AF.utils.create('div', { class: 'flex items-center gap-4 p-3 bg-forge-900/50 rounded-lg hover:bg-forge-900 transition-colors' }, [
            AF.utils.create('div', { class: 'w-10 h-10 rounded-lg bg-forge-800 border border-forge-700 flex items-center justify-center flex-shrink-0' }, [
                AF.utils.create('span', { class: 'text-xs font-mono text-forge-400' }, agent.id.slice(0, 3).toUpperCase()),
            ]),
            AF.utils.create('div', { class: 'flex-1 min-w-0' }, [
                AF.utils.create('div', { class: 'flex items-center gap-2 flex-wrap' }, [
                    AF.utils.create('span', { class: 'font-medium text-forge-100 truncate' }, agent.name),
                    AF.utils.create('span', { class: 'text-xs px-2 py-0.5 rounded-full bg-forge-800 text-forge-400' }, levelLabels[agent.level] || agent.level),
                    AF.utils.create('span', { class: 'text-xs px-2 py-0.5 rounded-full bg-forge-800 text-forge-500' }, agent.department || 'General'),
                ]),
                AF.utils.create('div', { class: 'flex items-center gap-3 mt-1 text-xs text-forge-500' }, [
                    AF.utils.create('span', { class: 'flex items-center gap-1' }, [
                        AF.utils.create('span', { class: `w-1.5 h-1.5 rounded-full ${statusColors[agent.status] || statusColors.offline}` }),
                        statusLabels[agent.status] || 'Unknown',
                    ]),
                    agent.current_task && AF.utils.create('span', { class: 'truncate max-w-xs' }, `Task: ${agent.current_task}`),
                ]),
            ]),
            AF.utils.create('div', { class: 'flex items-center gap-2' }, [
                AF.utils.create('button', { class: 'btn btn-ghost btn-sm', onclick: () => this.viewAgent(agent.id) }, 'View'),
            ]),
        ]);
    },

    viewAgent(agentId) {
        // TODO: Open agent detail modal
        AF.toast.info(`View agent ${agentId}`);
    },

    openCreateAgentModal() {
        const content = AF.utils.create('div', {}, [
            AF.utils.create('div', { class: 'modal-header' }, [
                AF.utils.create('h3', { class: 'modal-title' }, 'Create New Agent'),
            ]),
            AF.utils.create('div', { class: 'modal-body space-y-4' }, [
                AF.utils.create('div', {}, [
                    AF.utils.create('label', { class: 'block text-sm font-medium text-forge-300 mb-1' }, 'Name'),
                    AF.utils.create('input', { type: 'text', id: 'agent-name', class: 'w-full bg-forge-800 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500', placeholder: 'Agent name' }),
                ]),
                AF.utils.create('div', {}, [
                    AF.utils.create('label', { class: 'block text-sm font-medium text-forge-300 mb-1' }, 'Level'),
                    AF.utils.create('select', { id: 'agent-level', class: 'w-full bg-forge-800 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500' }, [
                        AF.utils.create('option', { value: 'worker' }, 'Worker'),
                        AF.utils.create('option', { value: 'team_leader' }, 'Team Leader'),
                        AF.utils.create('option', { value: 'head' }, 'Head'),
                        AF.utils.create('option', { value: 'principal' }, 'Principal'),
                    ]),
                ]),
                AF.utils.create('div', {}, [
                    AF.utils.create('label', { class: 'block text-sm font-medium text-forge-300 mb-1' }, 'Department'),
                    AF.utils.create('input', { type: 'text', id: 'agent-department', class: 'w-full bg-forge-800 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500', placeholder: 'Department' }),
                ]),
                AF.utils.create('div', {}, [
                    AF.utils.create('label', { class: 'block text-sm font-medium text-forge-300 mb-1' }, 'Model'),
                    AF.utils.create('select', { id: 'agent-model', class: 'w-full bg-forge-800 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500' }, [
                        AF.utils.create('option', { value: 'gpt-4o' }, 'GPT-4o'),
                        AF.utils.create('option', { value: 'gpt-4o-mini' }, 'GPT-4o Mini'),
                        AF.utils.create('option', { value: 'claude-3-5-sonnet' }, 'Claude 3.5 Sonnet'),
                        AF.utils.create('option', { value: 'llama-3.1-405b' }, 'Llama 3.1 405B'),
                    ]),
                ]),
            ]),
            AF.utils.create('div', { class: 'modal-footer' }, [
                AF.utils.create('button', { class: 'btn btn-secondary', onclick: () => AF.modal.closeAll() }, 'Cancel'),
                AF.utils.create('button', { class: 'btn btn-primary', onclick: () => this.createAgent() }, 'Create Agent'),
            ]),
        ]);
        AF.modal.open(content);
    },

    async createAgent() {
        const name = document.getElementById('agent-name')?.value;
        const level = document.getElementById('agent-level')?.value;
        const department = document.getElementById('agent-department')?.value;
        const model = document.getElementById('agent-model')?.value;

        if (!name) {
            AF.toast.error('Name is required');
            return;
        }

        try {
            await AF.utils.post('/agents', { name, level, department, model });
            AF.toast.success('Agent created');
            AF.modal.closeAll();
            await this.loadAgents();
            this.renderAgentList();
        } catch (error) {
            AF.toast.error(error.message);
        }
    },

    navItems = [
        { page: 'dashboard', label: 'Dashboard', route: AF.CONFIG.ROUTES.DASHBOARD, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' })]) },
        { page: 'chat', label: 'AI Chat', route: AF.CONFIG.ROUTES.CHAT, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' })]) },
        { page: 'agents', label: 'Agent Center', route: AF.CONFIG.ROUTES.AGENTS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' })]), active: true },
        { page: 'projects', label: 'Projects', route: AF.CONFIG.ROUTES.PROJECTS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z' })]) },
        { page: 'settings', label: 'Settings', route: AF.CONFIG.ROUTES.SETTINGS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' })]) },
    ],

    mount() {
        this.updateActiveNav();
    },

    updateActiveNav() {
        const currentPath = location.pathname;
        document.querySelectorAll('[data-page]').forEach(el => {
            const page = el.dataset.page;
            const isActive = currentPath === AF.CONFIG.ROUTES[page.toUpperCase()];
            el.classList.toggle('bg-accent-500/10', isActive);
            el.classList.toggle('text-accent-400', isActive);
            el.classList.toggle('text-forge-400', !isActive);
            el.classList.toggle('hover:text-forge-100', !isActive);
            el.classList.toggle('hover:bg-forge-800', !isActive);
        });
    },

    async unload() {
        // Cleanup
    },
};