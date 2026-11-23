/**
 * Projects Page - Project Management
 */
export default {
    projects: [],
    selectedProject: null,
    viewMode: 'grid', // 'grid' or 'list'

    async init() {
        if (!AF.auth.isAuthenticated()) {
            AF.router.navigate(AF.CONFIG.ROUTES.LOGIN, true);
            return;
        }
        await this.loadProjects();
    },

    async loadProjects() {
        try {
            const response = await AF.utils.get('/projects');
            this.projects = response.projects || [];
        } catch (error) {
            console.error('Failed to load projects:', error);
            this.projects = [];
        }
    },

    render() {
        return AF.utils.create('div', { class: 'min-h-screen', id: 'projects-page' }, [
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
                    AF.utils.create('h1', { class: 'text-lg font-semibold text-forge-50' }, 'Projects'),
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
                            AF.utils.create('h2', { class: 'text-2xl font-bold text-forge-50' }, 'Projects'),
                            AF.utils.create('p', { class: 'text-forge-400 mt-1' }, 'Manage your software engineering projects'),
                        ]),
                        AF.utils.create('button', { class: 'btn btn-primary', onclick: () => this.openCreateProjectModal() }, [
                            AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 4v16m8-8H4' })]),
                            ' New Project',
                        ]),
                    ]),

                    // View toggle
                    AF.utils.create('div', { class: 'flex items-center gap-2' }, [
                        AF.utils.create('div', { class: 'flex bg-forge-800 rounded-lg p-1' }, [
                            AF.utils.create('button', {
                                class: `btn btn-sm ${this.viewMode === 'grid' ? 'btn-primary' : 'btn-ghost'}`,
                                onclick: () => { this.viewMode = 'grid'; this.renderProjectGrid(); },
                            }, [
                                AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' })]),
                            ]),
                            AF.utils.create('button', {
                                class: `btn btn-sm ${this.viewMode === 'list' ? 'btn-primary' : 'btn-ghost'}`,
                                onclick: () => { this.viewMode = 'list'; this.renderProjectGrid(); },
                            }, [
                                AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 6h16M4 12h16M4 18h16' })]),
                            ]),
                        ]),
                    ]),

                    // Projects Grid/List
                    AF.utils.create('div', { class: 'card' }, [
                        AF.utils.create('div', { class: 'card-body p-0' }, [
                            AF.utils.create('div', { id: 'projects-container', class: this.viewMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4' : 'divide-y divide-forge-800' }),
                        ]),
                    ]),
                ]),
            ]),
        ]);
    },

    renderProjects() {
        const container = document.getElementById('projects-container');
        if (!container) return;

        container.innerHTML = '';

        if (this.projects.length === 0) {
            container.appendChild(AF.utils.create('div', { class: this.viewMode === 'grid' ? 'col-span-full' : '' }, [
                AF.utils.create('div', { class: 'flex flex-col items-center justify-center py-16 text-forge-500' }, [
                    AF.utils.create('svg', { class: 'w-16 h-16 mb-4 text-forge-700', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '1.5', d: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' })]),
                    AF.utils.create('h3', { class: 'text-lg font-medium mb-2' }, 'No projects yet'),
                    AF.utils.create('p', { class: 'text-sm text-center max-w-xs' }, 'Create your first project to start building with autonomous agents.'),
                    AF.utils.create('button', { class: 'btn btn-primary mt-4', onclick: () => this.openCreateProjectModal() }, 'Create Project'),
                ]),
            ]));
            return;
        }

        this.projects.forEach(project => {
            container.appendChild(this.renderProjectCard(project));
        });
    },

    renderProjectCard(project) {
        const statusColors = {
            active: 'bg-accent-500',
            paused: 'bg-warning-500',
            completed: 'bg-info-500',
            archived: 'bg-forge-500',
        };
        const statusLabels = {
            active: 'Active',
            paused: 'Paused',
            completed: 'Completed',
            archived: 'Archived',
        };

        if (this.viewMode === 'grid') {
            return AF.utils.create('div', { class: 'card h-full flex flex-col hover:border-forge-700 transition-colors' }, [
                AF.utils.create('div', { class: 'p-4' }, [
                    AF.utils.create('div', { class: 'flex items-start justify-between mb-3' }, [
                        AF.utils.create('div', { class: 'w-12 h-12 rounded-xl bg-forge-800 border border-forge-700 flex items-center justify-center' }, [
                            AF.utils.create('svg', { class: 'w-6 h-6 text-accent-500', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' })]),
                        ]),
                        AF.utils.create('span', { class: `w-2 h-2 rounded-full ${statusColors[project.status] || statusColors.active}` }),
                    ]),
                    AF.utils.create('h3', { class: 'font-semibold text-forge-100 mb-1 truncate' }, project.name),
                    AF.utils.create('p', { class: 'text-sm text-forge-400 mb-3 line-clamp-2' }, project.description || 'No description'),
                    AF.utils.create('div', { class: 'flex items-center gap-3 text-xs text-forge-500' }, [
                        AF.utils.create('span', { class: 'flex items-center gap-1' }, [
                            AF.utils.create('svg', { class: 'w-3.5 h-3.5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' })]),
                            AF.utils.formatRelative(project.updated_at || project.created_at),
                        ]),
                        AF.utils.create('span', { class: `px-2 py-0.5 rounded text-xs font-medium ${statusColors[project.status] || statusColors.active}/20 text-forge-100` }, statusLabels[project.status] || 'Active'),
                    ]),
                ]),
                AF.utils.create('div', { class: 'border-t border-forge-800 p-3 bg-forge-950/50' }, [
                    AF.utils.create('div', { class: 'flex items-center gap-2' }, [
                        AF.utils.create('button', { class: 'btn btn-primary btn-sm flex-1', onclick: () => this.openProject(project.id) }, 'Open'),
                        AF.utils.create('button', { class: 'btn btn-ghost btn-sm', onclick: () => this.openProjectMenu(project) }, [
                            AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z' })]),
                        ]),
                    ]),
                ]),
            ]);
        } else {
            // List view
            return AF.utils.create('div', { class: 'flex items-center gap-4 p-4 hover:bg-forge-900/50 transition-colors' }, [
                AF.utils.create('div', { class: 'w-12 h-12 rounded-xl bg-forge-800 border border-forge-700 flex items-center justify-center flex-shrink-0' }, [
                    AF.utils.create('svg', { class: 'w-6 h-6 text-accent-500', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' })]),
                ]),
                AF.utils.create('div', { class: 'flex-1 min-w-0' }, [
                    AF.utils.create('div', { class: 'flex items-center gap-2' }, [
                        AF.utils.create('h3', { class: 'font-semibold text-forge-100 truncate' }, project.name),
                        AF.utils.create('span', { class: `px-2 py-0.5 rounded text-xs font-medium ${statusColors[project.status] || statusColors.active}/20 text-forge-100` }, statusLabels[project.status] || 'Active'),
                    ]),
                    AF.utils.create('p', { class: 'text-sm text-forge-400 truncate mt-1' }, project.description || 'No description'),
                    AF.utils.create('div', { class: 'flex items-center gap-4 mt-2 text-xs text-forge-500' }, [
                        AF.utils.create('span', { class: 'flex items-center gap-1' }, [
                            AF.utils.create('svg', { class: 'w-3.5 h-3.5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' })]),
                            AF.utils.formatRelative(project.updated_at || project.created_at),
                        ]),
                        project.task_count !== undefined && AF.utils.create('span', { class: 'flex items-center gap-1' }, [
                            AF.utils.create('svg', { class: 'w-3.5 h-3.5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4' })]),
                            `${project.task_count} tasks`,
                        ]),
                    ]),
                ]),
                AF.utils.create('div', { class: 'flex items-center gap-2' }, [
                    AF.utils.create('button', { class: 'btn btn-primary btn-sm', onclick: () => this.openProject(project.id) }, 'Open'),
                    AF.utils.create('button', { class: 'btn btn-ghost btn-sm', onclick: () => this.openProjectMenu(project) }, [
                        AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z' })]),
                    ]),
                ]),
            ]);
        }
    },

    renderProjectGrid() {
        this.renderProjects();
    },

    openProject(projectId) {
        AF.router.navigate(`/projects/${projectId}`);
    },

    openProjectMenu(project) {
        const content = AF.utils.create('div', {}, [
            AF.utils.create('div', { class: 'modal-header' }, [
                AF.utils.create('h3', { class: 'modal-title' }, project.name),
            ]),
            AF.utils.create('div', { class: 'modal-body space-y-2' }, [
                AF.utils.create('button', { class: 'btn btn-secondary w-full justify-start', onclick: () => { AF.modal.closeAll(); this.openProject(project.id); } }, [
                    AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z' }),]),
                    ' Open Project',
                ]),
                AF.utils.create('button', { class: 'btn btn-secondary w-full justify-start', onclick: () => { AF.modal.closeAll(); this.editProject(project); } }, [
                    AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z' })]),
                    ' Edit',
                ]),
                AF.utils.create('button', { class: 'btn btn-secondary w-full justify-start', onclick: () => { AF.modal.closeAll(); this.openSettings(project.id); } }, [
                    AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' })]),
                    ' Settings',
                ]),
                AF.utils.create('button', { class: 'btn btn-secondary w-full justify-start text-danger-400 hover:bg-danger-500/10', onclick: () => { AF.modal.closeAll(); this.deleteProject(project.id); } }, [
                    AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16' })]),
                    ' Delete',
                ]),
            ]),
        ]);
        AF.modal.open(content);
    },

    openCreateProjectModal() {
        const content = AF.utils.create('div', {}, [
            AF.utils.create('div', { class: 'modal-header' }, [
                AF.utils.create('h3', { class: 'modal-title' }, 'Create New Project'),
            ]),
            AF.utils.create('div', { class: 'modal-body space-y-4' }, [
                AF.utils.create('div', {}, [
                    AF.utils.create('label', { class: 'block text-sm font-medium text-forge-300 mb-1' }, 'Project Name'),
                    AF.utils.create('input', { type: 'text', id: 'project-name', class: 'w-full bg-forge-800 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500', placeholder: 'My Awesome Project', required: true }),
                ]),
                AF.utils.create('div', {}, [
                    AF.utils.create('label', { class: 'block text-sm font-medium text-forge-300 mb-1' }, 'Description'),
                    AF.utils.create('textarea', { id: 'project-description', class: 'w-full bg-forge-800 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500', rows: 3, placeholder: 'Describe what this project is about...' }),
                ]),
                AF.utils.create('div', {}, [
                    AF.utils.create('label', { class: 'block text-sm font-medium text-forge-300 mb-1' }, 'Repository URL (optional)'),
                    AF.utils.create('input', { type: 'url', id: 'project-repo', class: 'w-full bg-forge-800 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500', placeholder: 'https://github.com/user/repo' }),
                ]),
            ]),
            AF.utils.create('div', { class: 'modal-footer' }, [
                AF.utils.create('button', { class: 'btn btn-secondary', onclick: () => AF.modal.closeAll() }, 'Cancel'),
                AF.utils.create('button', { class: 'btn btn-primary', onclick: () => this.createProject() }, 'Create Project'),
            ]),
        ]);
        AF.modal.open(content);
    },

    async createProject() {
        const name = document.getElementById('project-name')?.value;
        const description = document.getElementById('project-description')?.value;
        const repository_url = document.getElementById('project-repo')?.value;

        if (!name) {
            AF.toast.error('Project name is required');
            return;
        }

        try {
            await AF.utils.post('/projects', { name, description, repository_url });
            AF.toast.success('Project created');
            AF.modal.closeAll();
            await this.loadProjects();
            this.renderProjectGrid();
        } catch (error) {
            AF.toast.error(error.message);
        }
    },

    editProject(project) {
        const content = AF.utils.create('div', {}, [
            AF.utils.create('div', { class: 'modal-header' }, [
                AF.utils.create('h3', { class: 'modal-title' }, 'Edit Project'),
            ]),
            AF.utils.create('div', { class: 'modal-body space-y-4' }, [
                AF.utils.create('div', {}, [
                    AF.utils.create('label', { class: 'block text-sm font-medium text-forge-300 mb-1' }, 'Project Name'),
                    AF.utils.create('input', { type: 'text', id: 'edit-project-name', value: project.name, class: 'w-full bg-forge-800 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500' }),
                ]),
                AF.utils.create('div', {}, [
                    AF.utils.create('label', { class: 'block text-sm font-medium text-forge-300 mb-1' }, 'Description'),
                    AF.utils.create('textarea', { id: 'edit-project-description', class: 'w-full bg-forge-800 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500', rows: 3 }, project.description || ''),
                ]),
                AF.utils.create('div', {}, [
                    AF.utils.create('label', { class: 'block text-sm font-medium text-forge-300 mb-1' }, 'Repository URL'),
                    AF.utils.create('input', { type: 'url', id: 'edit-project-repo', value: project.repository_url || '', class: 'w-full bg-forge-800 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500' }),
                ]),
            ]),
            AF.utils.create('div', { class: 'modal-footer' }, [
                AF.utils.create('button', { class: 'btn btn-secondary', onclick: () => AF.modal.closeAll() }, 'Cancel'),
                AF.utils.create('button', { class: 'btn btn-primary', onclick: () => this.updateProject(project.id) }, 'Save Changes'),
            ]),
        ]);
        AF.modal.open(content);
    },

    async updateProject(projectId) {
        const name = document.getElementById('edit-project-name')?.value;
        const description = document.getElementById('edit-project-description')?.value;
        const repository_url = document.getElementById('edit-project-repo')?.value;

        try {
            await AF.utils.patch(`/projects/${projectId}`, { name, description, repository_url });
            AF.toast.success('Project updated');
            AF.modal.closeAll();
            await this.loadProjects();
            this.renderProjectGrid();
        } catch (error) {
            AF.toast.error(error.message);
        }
    },

    async deleteProject(projectId) {
        const confirmed = await AF.modal.confirm('Are you sure you want to delete this project? This action cannot be undone.', 'Delete Project');
        if (!confirmed) return;

        try {
            await AF.utils.delete(`/projects/${projectId}`);
            AF.toast.success('Project deleted');
            await this.loadProjects();
            this.renderProjectGrid();
        } catch (error) {
            AF.toast.error(error.message);
        }
    },

    openSettings(projectId) {
        AF.router.navigate(`/projects/${projectId}/settings`);
    },

    navItems = [
        { page: 'dashboard', label: 'Dashboard', route: AF.CONFIG.ROUTES.DASHBOARD, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' })]) },
        { page: 'chat', label: 'AI Chat', route: AF.CONFIG.ROUTES.CHAT, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' })]) },
        { page: 'agents', label: 'Agent Center', route: AF.CONFIG.ROUTES.AGENTS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' })]) },
        { page: 'projects', label: 'Projects', route: AF.CONFIG.ROUTES.PROJECTS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z' })]), active: true },
        { page: 'settings', label: 'Settings', route: AF.CONFIG.ROUTES.SETTINGS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' })]) },
    ],

    mount() {
        this.updateActiveNav();
        this.renderProjectGrid();
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