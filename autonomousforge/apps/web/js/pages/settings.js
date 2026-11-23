/**
 * Settings Page - Configuration
 */
export default {
    activeTab: 'general',
    user: null,
    apiKeys: [],
    providers: [],
    models: [],

    async init() {
        if (!AF.auth.isAuthenticated()) {
            AF.router.navigate(AF.CONFIG.ROUTES.LOGIN, true);
            return;
        }
        this.user = AF.auth.getUser();
        await this.loadData();
    },

    async loadData() {
        try {
            const [apiKeys, providers, models] = await Promise.all([
                AF.utils.get('/api-keys').catch(() => ({ keys: [] })),
                AF.utils.get('/providers').catch(() => ({ providers: [] })),
                AF.utils.get('/models').catch(() => ({ models: [] })),
            ]);
            this.apiKeys = apiKeys.keys || [];
            this.providers = providers.providers || [];
            this.models = models.models || [];
        } catch (error) {
            console.error('Failed to load settings data:', error);
        }
    },

    setTab(tab) {
        this.activeTab = tab;
        this.renderTabs();
        this.renderTabContent();
    },

    async saveGeneralSettings(data) {
        try {
            await AF.utils.patch('/auth/me', data);
            this.user = { ...this.user, ...data };
            AF.toast.success('Settings saved');
        } catch (error) {
            AF.toast.error(error.message);
        }
    },

    async addApiKey() {
        const name = prompt('API Key name:');
        if (!name) return;

        const provider = prompt('Provider (openai, anthropic, nvidia, etc.):');
        if (!provider) return;

        const key = prompt('API Key value:');
        if (!key) return;

        try {
            await AF.utils.post('/api-keys', { name, provider, key });
            AF.toast.success('API key added');
            await this.loadData();
            this.renderTabContent();
        } catch (error) {
            AF.toast.error(error.message);
        }
    },

    async deleteApiKey(keyId) {
        if (!confirm('Delete this API key?')) return;
        try {
            await AF.utils.delete(`/api-keys/${keyId}`);
            AF.toast.success('API key deleted');
            await this.loadData();
            this.renderTabContent();
        } catch (error) {
            AF.toast.error(error.message);
        }
    },

    async testProvider(providerId) {
        try {
            await AF.utils.post(`/providers/${providerId}/test`);
            AF.toast.success('Provider connection successful');
        } catch (error) {
            AF.toast.error(error.message);
        }
    },

    async saveProviderConfig(providerId, config) {
        try {
            await AF.utils.patch(`/providers/${providerId}`, config);
            AF.toast.success('Provider config saved');
            await this.loadData();
            this.renderTabContent();
        } catch (error) {
            AF.toast.error(error.message);
        }
    },

    async changePassword(currentPassword, newPassword) {
        try {
            await AF.utils.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword });
            AF.toast.success('Password changed');
        } catch (error) {
            AF.toast.error(error.message);
        }
    },

    async enable2FA() {
        try {
            const response = await AF.utils.post('/auth/2fa/enable');
            return response;
        } catch (error) {
            AF.toast.error(error.message);
            return null;
        }
    },

    async disable2FA(password) {
        try {
            await AF.utils.post('/auth/2fa/disable', { password });
            AF.toast.success('2FA disabled');
        } catch (error) {
            AF.toast.error(error.message);
        }
    },

    render() {
        return AF.utils.create('div', { class: 'min-h-screen flex flex-col', id: 'settings-page' }, [
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
                AF.utils.create('div', { class: 'flex-1 flex items-center justify-center' }, [
                    AF.utils.create('h1', { class: 'text-lg font-semibold text-forge-50' }, 'Settings'),
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
                AF.utils.create('div', { class: 'p-4 lg:p-6' }, [
                    // Page header
                    AF.utils.create('div', { class: 'mb-6' }, [
                        AF.utils.create('h2', { class: 'text-2xl font-bold text-forge-50' }, 'Settings'),
                        AF.utils.create('p', { class: 'text-forge-400 mt-1' }, 'Configure your AUTONOMOUSFORGE instance'),
                    ]),

                    // Tabs
                    AF.utils.create('div', { class: 'border-b border-forge-800 mb-6', role: 'tablist' }, [
                        AF.utils.create('nav', { class: 'flex gap-1 overflow-x-auto', id: 'settings-tabs' }, this.tabs.map(tab =>
                            AF.utils.create('button', {
                                role: 'tab',
                                'aria-selected': tab.id === this.activeTab,
                                class: `px-4 py-3 rounded-t-lg text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${tab.id === this.activeTab ? 'border-accent-500 text-accent-400' : 'border-transparent text-forge-500 hover:text-forge-100 hover:border-forge-700'}`,
                                onclick: () => this.setTab(tab.id),
                            }, tab.label)
                        )),
                    ]),

                    // Tab content
                    AF.utils.create('div', { id: 'settings-tab-content', role: 'tabpanel' }),
                ]),
            ]),
        ]);
    },

    renderTabs() {
        const container = document.getElementById('settings-tabs');
        if (!container) return;
        container.innerHTML = '';
        this.tabs.forEach(tab => {
            container.appendChild(AF.utils.create('button', {
                role: 'tab',
                'aria-selected': tab.id === this.activeTab,
                class: `px-4 py-3 rounded-t-lg text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${tab.id === this.activeTab ? 'border-accent-500 text-accent-400' : 'border-transparent text-forge-500 hover:text-forge-100 hover:border-forge-700'}`,
                onclick: () => this.setTab(tab.id),
            }, tab.label));
        });
    },

    renderTabContent() {
        const container = document.getElementById('settings-tab-content');
        if (!container) return;

        container.innerHTML = '';

        switch (this.activeTab) {
            case 'general':
                container.appendChild(this.renderGeneralTab());
                break;
            case 'security':
                container.appendChild(this.renderSecurityTab());
                break;
            case 'api-keys':
                container.appendChild(this.renderApiKeysTab());
                break;
            case 'providers':
                container.appendChild(this.renderProvidersTab());
                break;
            case 'models':
                container.appendChild(this.renderModelsTab());
                break;
            case 'appearance':
                container.appendChild(this.renderAppearanceTab());
                break;
            case 'advanced':
                container.appendChild(this.renderAdvancedTab());
                break;
        }
    },

    renderGeneralTab() {
        return AF.utils.create('div', { class: 'max-w-2xl space-y-6' }, [
            AF.utils.create('div', { class: 'card' }, [
                AF.utils.create('div', { class: 'card-header' }, [
                    AF.utils.create('h3', { class: 'font-semibold' }, 'Profile'),
                ]),
                AF.utils.create('div', { class: 'card-body space-y-4' }, [
                    AF.utils.create('div', { class: 'flex items-center gap-4' }, [
                        AF.utils.create('div', { class: 'w-20 h-20 rounded-xl bg-forge-800 border border-forge-700 flex items-center justify-center text-2xl font-semibold text-forge-300' }, this.user?.display_name?.[0]?.toUpperCase() || 'O'),
                        AF.utils.create('div', {}, [
                            AF.utils.create('h4', { class: 'font-semibold text-forge-100' }, this.user?.display_name || 'Owner'),
                            AF.utils.create('p', { class: 'text-forge-400' }, this.user?.email || ''),
                            AF.utils.create('p', { class: 'text-xs text-forge-500 font-mono mt-1' }, this.user?.id || ''),
                        ]),
                    ]),
                    AF.utils.create('div', { class: 'grid gap-4 sm:grid-cols-2' }, [
                        AF.utils.create('div', {}, [
                            AF.utils.create('label', { class: 'block text-sm text-forge-400 mb-1' }, 'Display Name'),
                            AF.utils.create('input', {
                                type: 'text',
                                id: 'display-name',
                                class: 'w-full bg-forge-900 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500',
                                value: this.user?.display_name || '',
                                onchange: (e) => this.saveGeneralSettings({ display_name: e.target.value }),
                            }),
                        ]),
                        AF.utils.create('div', {}, [
                            AF.utils.create('label', { class: 'block text-sm text-forge-400 mb-1' }, 'Email'),
                            AF.utils.create('input', {
                                type: 'email',
                                id: 'email',
                                class: 'w-full bg-forge-900 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500',
                                value: this.user?.email || '',
                                onchange: (e) => this.saveGeneralSettings({ email: e.target.value }),
                            }),
                        ]),
                    ]),
                ]),
            ]),

            AF.utils.create('div', { class: 'card' }, [
                AF.utils.create('div', { class: 'card-header' }, [
                    AF.utils.create('h3', { class: 'font-semibold' }, 'Preferences'),
                ]),
                AF.utils.create('div', { class: 'card-body space-y-4' }, [
                    AF.utils.create('label', { class: 'flex items-center justify-between' }, [
                        AF.utils.create('div', {}, [
                            AF.utils.create('p', { class: 'font-medium text-forge-100' }, 'Dark Mode'),
                            AF.utils.create('p', { class: 'text-sm text-forge-500' }, 'Use dark theme (requires reload)'),
                        ]),
                        AF.utils.create('input', {
                            type: 'checkbox',
                            class: 'w-5 h-5 rounded border-forge-700 bg-forge-800 text-accent-500 focus:ring-accent-500',
                            checked: AF.state.theme === 'dark',
                            onchange: (e) => AF.ui.setTheme(e.target.checked ? 'dark' : 'light'),
                        }),
                    ]),
                    AF.utils.create('label', { class: 'flex items-center justify-between' }, [
                        AF.utils.create('div', {}, [
                            AF.utils.create('p', { class: 'font-medium text-forge-100' }, 'Auto-save Chats'),
                            AF.utils.create('p', { class: 'text-sm text-forge-500' }, 'Automatically save chat history'),
                        ]),
                        AF.utils.create('input', { type: 'checkbox', class: 'w-5 h-5 rounded border-forge-700 bg-forge-800 text-accent-500 focus:ring-accent-500', checked: true }),
                    ]),
                    AF.utils.create('label', { class: 'flex items-center justify-between' }, [
                        AF.utils.create('div', {}, [
                            AF.utils.create('p', { class: 'font-medium text-forge-100' }, 'WebSocket Notifications'),
                            AF.utils.create('p', { class: 'text-sm text-forge-500' }, 'Receive real-time updates'),
                        ]),
                        AF.utils.create('input', { type: 'checkbox', class: 'w-5 h-5 rounded border-forge-700 bg-forge-800 text-accent-500 focus:ring-accent-500', checked: true }),
                    ]),
                ]),
            ]),
        ]);
    },

    renderSecurityTab() {
        const has2FA = this.user?.two_factor_enabled || false;

        return AF.utils.create('div', { class: 'max-w-2xl space-y-6' }, [
            AF.utils.create('div', { class: 'card' }, [
                AF.utils.create('div', { class: 'card-header' }, [
                    AF.utils.create('h3', { class: 'font-semibold' }, 'Two-Factor Authentication'),
                ]),
                AF.utils.create('div', { class: 'card-body space-y-4' }, [
                    AF.utils.create('div', { class: 'flex items-center justify-between' }, [
                        AF.utils.create('div', {}, [
                            AF.utils.create('p', { class: 'font-medium text-forge-100' }, '2FA Status'),
                            AF.utils.create('p', { class: 'text-sm text-forge-500' }, has2FA ? 'Enabled - Secure' : 'Disabled - Recommended to enable'),
                        ]),
                        has2FA
                            ? AF.utils.create('button', { class: 'btn btn-danger', onclick: () => this.confirmDisable2FA() }, 'Disable 2FA')
                            : AF.utils.create('button', { class: 'btn btn-primary', onclick: () => this.setup2FA() }, 'Enable 2FA'),
                    ]),
                    has2FA && AF.utils.create('div', { class: 'p-3 bg-forge-900/50 rounded-lg border border-forge-800' }, [
                        AF.utils.create('p', { class: 'text-sm text-forge-300' }, 'Two-factor authentication is enabled. You will need your authenticator app to log in.'),
                    ]),
                ]),
            ]),

            AF.utils.create('div', { class: 'card' }, [
                AF.utils.create('div', { class: 'card-header' }, [
                    AF.utils.create('h3', { class: 'font-semibold' }, 'Change Password'),
                ]),
                AF.utils.create('div', { class: 'card-body space-y-4' }, [
                    AF.utils.create('form', { id: 'password-form', onsubmit: (e) => this.handlePasswordChange(e) }, [
                        AF.utils.create('div', {}, [
                            AF.utils.create('label', { class: 'block text-sm text-forge-400 mb-1' }, 'Current Password'),
                            AF.utils.create('input', { type: 'password', id: 'current-password', class: 'w-full bg-forge-900 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500', required: true }),
                        ]),
                        AF.utils.create('div', {}, [
                            AF.utils.create('label', { class: 'block text-sm text-forge-400 mb-1' }, 'New Password'),
                            AF.utils.create('input', { type: 'password', id: 'new-password', class: 'w-full bg-forge-900 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500', required: true, minlength: 8 }),
                        ]),
                        AF.utils.create('div', {}, [
                            AF.utils.create('label', { class: 'block text-sm text-forge-400 mb-1' }, 'Confirm New Password'),
                            AF.utils.create('input', { type: 'password', id: 'confirm-password', class: 'w-full bg-forge-900 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500', required: true }),
                        ]),
                        AF.utils.create('button', { type: 'submit', class: 'btn btn-primary' }, 'Change Password'),
                    ]),
                ]),
            ]),

            AF.utils.create('div', { class: 'card' }, [
                AF.utils.create('div', { class: 'card-header' }, [
                    AF.utils.create('h3', { class: 'font-semibold' }, 'Active Sessions'),
                ]),
                AF.utils.create('div', { class: 'card-body' }, [
                    AF.utils.create('p', { class: 'text-forge-400 text-sm' }, 'Session management will be available after backend integration.'),
                    AF.utils.create('button', { class: 'btn btn-secondary mt-4', onclick: () => AF.auth.logout().then(() => AF.router.navigate(AF.CONFIG.ROUTES.LOGIN)) }, 'Log out of all sessions'),
                ]),
            ]),
        ]);
    },

    renderApiKeysTab() {
        return AF.utils.create('div', { class: 'max-w-4xl space-y-6' }, [
            AF.utils.create('div', { class: 'flex items-center justify-between' }, [
                AF.utils.create('h3', { class: 'text-lg font-semibold' }, 'API Keys'),
                AF.utils.create('button', { class: 'btn btn-primary', onclick: () => this.addApiKey() }, [
                    AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 6v6m0 0v6m0-6h6m-6 0H6' })]),
                    ' Add API Key',
                ]),
            ]),
            AF.utils.create('p', { class: 'text-forge-400 text-sm' }, 'Store encrypted API keys for external providers. Keys are encrypted at rest with your master key.'),

            this.apiKeys.length > 0
                ? AF.utils.create('div', { class: 'space-y-3' }, this.apiKeys.map(key =>
                    AF.utils.create('div', { class: 'card p-4 flex items-center justify-between' }, [
                        AF.utils.create('div', { class: 'flex items-center gap-4' }, [
                            AF.utils.create('div', { class: 'w-10 h-10 rounded-lg bg-forge-800 border border-forge-700 flex items-center justify-center' }, [
                                AF.utils.create('svg', { class: 'w-5 h-5 text-forge-400', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z' })]),
                            ]),
                            AF.utils.create('div', {}, [
                                AF.utils.create('p', { class: 'font-medium text-forge-100' }, key.name),
                                AF.utils.create('p', { class: 'text-sm text-forge-500' }, `${key.provider} • ${key.last_used ? AF.utils.formatRelative(key.last_used) : 'Never used'}`),
                            ]),
                        ]),
                        AF.utils.create('div', { class: 'flex items-center gap-2' }, [
                            AF.utils.create('span', { class: `px-2 py-0.5 rounded-full text-xs font-medium ${key.is_active ? 'bg-accent-500/20 text-accent-400' : 'bg-forge-700 text-forge-400'}` }, key.is_active ? 'Active' : 'Inactive'),
                            AF.utils.create('button', { class: 'btn btn-ghost btn-icon text-forge-500 hover:text-danger-400', onclick: () => this.deleteApiKey(key.id), 'aria-label': 'Delete API key' }, [
                                AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16' })]),
                            ]),
                        ]),
                    ])
                ))
                : AF.utils.create('div', { class: 'card p-8 text-center' }, [
                    AF.utils.create('svg', { class: 'w-12 h-12 mx-auto mb-4 text-forge-700', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '1.5', d: 'M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z' })]),
                    AF.utils.create('h4', { class: 'font-medium text-forge-300 mb-1' }, 'No API keys configured'),
                    AF.utils.create('p', { class: 'text-forge-500 text-sm mb-4' }, 'Add your first API key to integrate with external providers'),
                    AF.utils.create('button', { class: 'btn btn-primary', onclick: () => this.addApiKey() }, 'Add API Key'),
                ]),
        ]);
    },

    renderProvidersTab() {
        return AF.utils.create('div', { class: 'max-w-4xl space-y-6' }, [
            AF.utils.create('h3', { class: 'text-lg font-semibold' }, 'Providers'),
            AF.utils.create('p', { class: 'text-forge-400 text-sm' }, 'Configure AI model providers. Each provider can have multiple models.'),

            this.providers.length > 0
                ? AF.utils.create('div', { class: 'space-y-4' }, this.providers.map(provider =>
                    AF.utils.create('div', { class: 'card' }, [
                        AF.utils.create('div', { class: 'card-header flex items-center justify-between' }, [
                            AF.utils.create('div', { class: 'flex items-center gap-3' }, [
                                AF.utils.create('div', { class: 'w-10 h-10 rounded-lg bg-forge-800 border border-forge-700 flex items-center justify-center' }, [
                                    AF.utils.create('span', { class: 'font-semibold text-forge-400' }, provider.name.slice(0, 2).toUpperCase()),
                                ]),
                                AF.utils.create('div', {}, [
                                    AF.utils.create('h4', { class: 'font-medium text-forge-100' }, provider.name),
                                    AF.utils.create('p', { class: 'text-sm text-forge-500' }, `${provider.type} • ${provider.models?.length || 0} models`),
                                ]),
                            ]),
                            AF.utils.create('div', { class: 'flex items-center gap-2' }, [
                                AF.utils.create('span', { class: `px-2 py-0.5 rounded-full text-xs font-medium ${provider.enabled ? 'bg-accent-500/20 text-accent-400' : 'bg-forge-700 text-forge-400'}` }, provider.enabled ? 'Enabled' : 'Disabled'),
                                AF.utils.create('button', { class: 'btn btn-ghost btn-sm', onclick: () => this.testProvider(provider.id) }, 'Test'),
                            ]),
                        ]),
                        AF.utils.create('div', { class: 'card-body' }, [
                            AF.utils.create('div', { class: 'grid gap-4 sm:grid-cols-2' }, [
                                AF.utils.create('div', {}, [
                                    AF.utils.create('label', { class: 'block text-sm text-forge-400 mb-1' }, 'Base URL'),
                                    AF.utils.create('input', {
                                        type: 'url',
                                        class: 'w-full bg-forge-900 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500',
                                        value: provider.base_url || '',
                                        onchange: (e) => this.saveProviderConfig(provider.id, { base_url: e.target.value }),
                                    }),
                                ]),
                                AF.utils.create('div', {}, [
                                    AF.utils.create('label', { class: 'block text-sm text-forge-400 mb-1' }, 'Timeout (ms)'),
                                    AF.utils.create('input', {
                                        type: 'number',
                                        class: 'w-full bg-forge-900 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500',
                                        value: provider.timeout || 30000,
                                        onchange: (e) => this.saveProviderConfig(provider.id, { timeout: parseInt(e.target.value) }),
                                    }),
                                ]),
                            ]),
                            AF.utils.create('div', { class: 'flex items-center gap-4 mt-4 pt-4 border-t border-forge-800' }, [
                                AF.utils.create('label', { class: 'flex items-center gap-2' }, [
                                    AF.utils.create('input', { type: 'checkbox', class: 'w-4 h-4 rounded border-forge-700 bg-forge-800 text-accent-500 focus:ring-accent-500', checked: provider.enabled, onchange: (e) => this.saveProviderConfig(provider.id, { enabled: e.target.checked }) }),
                                    AF.utils.create('span', { class: 'text-sm text-forge-300' }, 'Enabled'),
                                ]),
                            ]),
                        ]),
                    ])
                ))
                : AF.utils.create('div', { class: 'card p-8 text-center' }, [
                    AF.utils.create('svg', { class: 'w-12 h-12 mx-auto mb-4 text-forge-700', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '1.5', d: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4' })]),
                    AF.utils.create('h4', { class: 'font-medium text-forge-300 mb-1' }, 'No providers configured'),
                    AF.utils.create('p', { class: 'text-forge-500 text-sm' }, 'Providers will appear here after configuration'),
                ]),
        ]);
    },

    renderModelsTab() {
        return AF.utils.create('div', { class: 'max-w-4xl space-y-6' }, [
            AF.utils.create('h3', { class: 'text-lg font-semibold' }, 'Models'),
            AF.utils.create('p', { class: 'text-forge-400 text-sm' }, 'Available AI models from configured providers.'),

            this.models.length > 0
                ? AF.utils.create('div', { class: 'overflow-x-auto' }, [
                    AF.utils.create('table', { class: 'w-full text-sm' }, [
                        AF.utils.create('thead', {}, [
                            AF.utils.create('tr', { class: 'text-left text-forge-500 border-b border-forge-800' }, [
                                AF.utils.create('th', { class: 'pb-3 font-medium' }, 'Model'),
                                AF.utils.create('th', { class: 'pb-3 font-medium' }, 'Provider'),
                                AF.utils.create('th', { class: 'pb-3 font-medium' }, 'Type'),
                                AF.utils.create('th', { class: 'pb-3 font-medium' }, 'Context'),
                                AF.utils.create('th', { class: 'pb-3 font-medium' }, 'Status'),
                            ]),
                        ]),
                        AF.utils.create('tbody', {}, this.models.map(model =>
                            AF.utils.create('tr', { class: 'border-b border-forge-800/50' }, [
                                AF.utils.create('td', { class: 'py-3 font-mono text-forge-100' }, model.id),
                                AF.utils.create('td', { class: 'py-3 text-forge-400' }, model.provider),
                                AF.utils.create('td', { class: 'py-3' }, [
                                    AF.utils.create('span', { class: `px-2 py-0.5 rounded-full text-xs font-medium ${model.type === 'chat' ? 'bg-info-500/20 text-info-400' : 'bg-purple-500/20 text-purple-400'}` }, model.type),
                                ]),
                                AF.utils.create('td', { class: 'py-3 text-forge-500 font-mono' }, model.context_length ? `${(model.context_length / 1000).toFixed(0)}k` : '—'),
                                AF.utils.create('td', { class: 'py-3' }, [
                                    AF.utils.create('span', { class: `px-2 py-0.5 rounded-full text-xs font-medium ${model.enabled ? 'bg-accent-500/20 text-accent-400' : 'bg-forge-700 text-forge-400'}` }, model.enabled ? 'Enabled' : 'Disabled'),
                                ]),
                            ])
                        )),
                    ]),
                ])
                : AF.utils.create('div', { class: 'card p-8 text-center' }, [
                    AF.utils.create('svg', { class: 'w-12 h-12 mx-auto mb-4 text-forge-700', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '1.5', d: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' })]),
                    AF.utils.create('h4', { class: 'font-medium text-forge-300 mb-1' }, 'No models available'),
                    AF.utils.create('p', { class: 'text-forge-500 text-sm' }, 'Configure providers to see available models'),
                ]),
        ]);
    },

    renderAppearanceTab() {
        return AF.utils.create('div', { class: 'max-w-2xl space-y-6' }, [
            AF.utils.create('div', { class: 'card' }, [
                AF.utils.create('div', { class: 'card-header' }, [
                    AF.utils.create('h3', { class: 'font-semibold' }, 'Theme'),
                ]),
                AF.utils.create('div', { class: 'card-body space-y-4' }, [
                    AF.utils.create('p', { class: 'text-forge-400' }, 'Choose your preferred color scheme.'),
                    AF.utils.create('div', { class: 'grid grid-cols-3 gap-3' }, [
                        AF.utils.create('button', { class: `card p-4 ${AF.state.theme === 'dark' ? 'border-accent-500/50 bg-accent-500/5' : ''}`, onclick: () => AF.ui.setTheme('dark') }, [
                            AF.utils.create('div', { class: 'w-16 h-16 rounded-lg bg-forge-950 border border-forge-800 mx-auto mb-3 flex items-center justify-center' }, [
                                AF.utils.create('svg', { class: 'w-8 h-8 text-accent-500', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z' })]),
                            ]),
                            AF.utils.create('p', { class: 'text-center font-medium' }, 'Dark'),
                        ]),
                        AF.utils.create('button', { class: `card p-4 ${AF.state.theme === 'light' ? 'border-accent-500/50 bg-accent-500/5' : ''}`, onclick: () => AF.ui.setTheme('light') }, [
                            AF.utils.create('div', { class: 'w-16 h-16 rounded-lg bg-forge-100 border border-forge-300 mx-auto mb-3 flex items-center justify-center' }, [
                                AF.utils.create('svg', { class: 'w-8 h-8 text-warning-500', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z' })]),
                            ]),
                            AF.utils.create('p', { class: 'text-center font-medium' }, 'Light'),
                        ]),
                        AF.utils.create('button', { class: `card p-4 ${AF.state.theme === 'system' ? 'border-accent-500/50 bg-accent-500/5' : ''}`, onclick: () => AF.ui.setTheme('system') }, [
                            AF.utils.create('div', { class: 'w-16 h-16 rounded-lg bg-gradient-to-br from-forge-950 to-forge-100 border border-forge-800 mx-auto mb-3 flex items-center justify-center' }, [
                                AF.utils.create('svg', { class: 'w-8 h-8 text-info-500', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' })]),
                            ]),
                            AF.utils.create('p', { class: 'text-center font-medium' }, 'System'),
                        ]),
                    ]),
                ]),
            ]),

            AF.utils.create('div', { class: 'card' }, [
                AF.utils.create('div', { class: 'card-header' }, [
                    AF.utils.create('h3', { class: 'font-semibold' }, 'Accent Color'),
                ]),
                AF.utils.create('div', { class: 'card-body' }, [
                    AF.utils.create('p', { class: 'text-forge-400 mb-4' }, 'Choose the accent color used throughout the interface.'),
                    AF.utils.create('div', { class: 'flex flex-wrap gap-3' }, this.accentColors.map(color =>
                        AF.utils.create('button', {
                            class: `w-10 h-10 rounded-lg border-2 transition-all ${AF.state.accentColor === color.value ? 'border-accent-500 scale-110' : 'border-forge-700 hover:border-forge-600'}`,
                            style: `background-color: ${color.value}`,
                            onclick: () => this.setAccentColor(color.value),
                            'aria-label': color.name,
                        })
                    )),
                ]),
            ]),
        ]);
    },

    renderAdvancedTab() {
        return AF.utils.create('div', { class: 'max-w-2xl space-y-6' }, [
            AF.utils.create('div', { class: 'card' }, [
                AF.utils.create('div', { class: 'card-header' }, [
                    AF.utils.create('h3', { class: 'font-semibold' }, 'Data & Storage'),
                ]),
                AF.utils.create('div', { class: 'card-body space-y-4' }, [
                    AF.utils.create('div', { class: 'flex items-center justify-between' }, [
                        AF.utils.create('div', {}, [
                            AF.utils.create('p', { class: 'font-medium text-forge-100' }, 'Export Data'),
                            AF.utils.create('p', { class: 'text-sm text-forge-500' }, 'Download all your data as JSON'),
                        ]),
                        AF.utils.create('button', { class: 'btn btn-secondary', onclick: () => this.exportData() }, 'Export'),
                    ]),
                    AF.utils.create('div', { class: 'flex items-center justify-between' }, [
                        AF.utils.create('div', {}, [
                            AF.utils.create('p', { class: 'font-medium text-forge-100' }, 'Clear Cache'),
                            AF.utils.create('p', { class: 'text-sm text-forge-500' }, 'Clear local storage and cached data'),
                        ]),
                        AF.utils.create('button', { class: 'btn btn-ghost', onclick: () => this.clearCache() }, 'Clear'),
                    ]),
                ]),
            ]),

            AF.utils.create('div', { class: 'card' }, [
                AF.utils.create('div', { class: 'card-header' }, [
                    AF.utils.create('h3', { class: 'font-semibold' }, 'Danger Zone'),
                ]),
                AF.utils.create('div', { class: 'card-body space-y-4' }, [
                    AF.utils.create('div', { class: 'flex items-center justify-between' }, [
                        AF.utils.create('div', {}, [
                            AF.utils.create('p', { class: 'font-medium text-danger-400' }, 'Delete Account'),
                            AF.utils.create('p', { class: 'text-sm text-forge-500' }, 'Permanently delete your account and all data'),
                        ]),
                        AF.utils.create('button', { class: 'btn btn-danger', onclick: () => this.confirmDeleteAccount() }, 'Delete Account'),
                    ]),
                ]),
            ]),

            AF.utils.create('div', { class: 'card' }, [
                AF.utils.create('div', { class: 'card-header' }, [
                    AF.utils.create('h3', { class: 'font-semibold' }, 'Version Info'),
                ]),
                AF.utils.create('div', { class: 'card-body' }, [
                    AF.utils.create('div', { class: 'grid gap-2 sm:grid-cols-2 text-sm' }, [
                        AF.utils.create('div', {}, [AF.utils.create('span', { class: 'text-forge-500' }, 'Version: '), AF.utils.create('span', { class: 'font-mono text-forge-300' }, '1.0.0')]),
                        AF.utils.create('div', {}, [AF.utils.create('span', { class: 'text-forge-500' }, 'Build: '), AF.utils.create('span', { class: 'font-mono text-forge-300' }, '2026.11.22')]),
                        AF.utils.create('div', {}, [AF.utils.create('span', { class: 'text-forge-500' }, 'Environment: '), AF.utils.create('span', { class: 'font-mono text-forge-300' }, 'Production')]),
                        AF.utils.create('div', {}, [AF.utils.create('span', { class: 'text-forge-500' }, 'Node: '), AF.utils.create('span', { class: 'font-mono text-forge-300' }, navigator.userAgent.slice(0, 50))]),
                    ]),
                ]),
            ]),
        ]);
    },

    tabs = [
        { id: 'general', label: 'General' },
        { id: 'security', label: 'Security' },
        { id: 'api-keys', label: 'API Keys' },
        { id: 'providers', label: 'Providers' },
        { id: 'models', label: 'Models' },
        { id: 'appearance', label: 'Appearance' },
        { id: 'advanced', label: 'Advanced' },
    ],

    accentColors = [
        { name: 'Green', value: '#22c55e' },
        { name: 'Blue', value: '#3b82f6' },
        { name: 'Purple', value: '#a855f7' },
        { name: 'Pink', value: '#ec4899' },
        { name: 'Orange', value: '#f97316' },
        { name: 'Cyan', value: '#06b6d4' },
    ],

    navItems = [
        { page: 'dashboard', label: 'Dashboard', route: AF.CONFIG.ROUTES.DASHBOARD, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' })]) },
        { page: 'chat', label: 'AI Chat', route: AF.CONFIG.ROUTES.CHAT, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' })]) },
        { page: 'agents', label: 'Agent Center', route: AF.CONFIG.ROUTES.AGENTS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' })]) },
        { page: 'projects', label: 'Projects', route: AF.CONFIG.ROUTES.PROJECTS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z' })]) },
        { page: 'settings', label: 'Settings', route: AF.CONFIG.ROUTES.SETTINGS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' })]), active: true },
    ],

    mount() {
        this.updateActiveNav();
        this.renderTabs();
        this.renderTabContent();
    },

    updateActiveNav() {
        const currentPath = location.pathname;
        document.querySelectorAll('[data-page]').forEach(el => {
            const page = el.dataset.page;
            const isActive = currentPath === AF.CONFIG.ROUTES[page.toUpperCase()] || currentPath.startsWith('/settings');
            el.classList.toggle('bg-accent-500/10', isActive);
            el.classList.toggle('text-accent-400', isActive);
            el.classList.toggle('text-forge-400', !isActive);
            el.classList.toggle('hover:text-forge-100', !isActive);
            el.classList.toggle('hover:bg-forge-800', !isActive);
        });
    },

    handlePasswordChange(e) {
        e.preventDefault();
        const current = document.getElementById('current-password').value;
        const newPass = document.getElementById('new-password').value;
        const confirm = document.getElementById('confirm-password').value;

        if (newPass !== confirm) {
            AF.toast.error('Passwords do not match');
            return;
        }
        if (newPass.length < 8) {
            AF.toast.error('Password must be at least 8 characters');
            return;
        }

        this.changePassword(current, newPass);
        document.getElementById('password-form').reset();
    },

    async setup2FA() {
        const result = await this.enable2FA();
        if (result) {
            AF.modal.open(AF.utils.create('div', { class: 'space-y-4' }, [
                AF.utils.create('h4', { class: 'font-semibold' }, 'Scan QR Code'),
                AF.utils.create('div', { class: 'flex justify-center' }, [
                    AF.utils.create('img', { src: result.qr_code, alt: '2FA QR Code', class: 'w-48 h-48 bg-forge-900 p-4 rounded-lg' }),
                ]),
                AF.utils.create('p', { class: 'text-sm text-forge-400' }, 'Scan with your authenticator app, then enter the code below.'),
                AF.utils.create('input', { type: 'text', id: '2fa-code', class: 'w-full bg-forge-900 border border-forge-700 rounded-lg px-3 py-2 text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500 text-center text-2xl tracking-widest', placeholder: '000000', maxlength: 6 }),
                AF.utils.create('div', { class: 'flex gap-2' }, [
                    AF.utils.create('button', { class: 'btn btn-secondary flex-1', onclick: () => AF.modal.closeAll() }, 'Cancel'),
                    AF.utils.create('button', { class: 'btn btn-primary flex-1', onclick: () => this.verify2FA(document.getElementById('2fa-code').value) }, 'Verify & Enable'),
                ]),
            ]));
        }
    },

    async verify2FA(code) {
        try {
            await AF.utils.post('/auth/2fa/verify', { code });
            AF.toast.success('2FA enabled');
            AF.modal.closeAll();
            await this.loadData();
            this.renderTabContent();
        } catch (error) {
            AF.toast.error(error.message);
        }
    },

    confirmDisable2FA() {
        const password = prompt('Enter your password to disable 2FA:');
        if (password) {
            this.disable2FA(password);
        }
    },

    confirmDeleteAccount() {
        AF.modal.confirm('This will permanently delete your account and ALL data. This action cannot be undone. Type "DELETE" to confirm.', 'Delete Account')
            .then(confirmed => {
                if (confirmed) {
                    const confirmText = prompt('Type "DELETE" to confirm:');
                    if (confirmText === 'DELETE') {
                        this.deleteAccount();
                    }
                }
            });
    },

    async deleteAccount() {
        try {
            await AF.utils.delete('/auth/me');
            AF.toast.success('Account deleted');
            AF.auth.logout();
            AF.router.navigate(AF.CONFIG.ROUTES.LOGIN);
        } catch (error) {
            AF.toast.error(error.message);
        }
    },

    exportData() {
        const data = {
            user: this.user,
            settings: {
                theme: AF.state.theme,
                // Add more settings as needed
            },
            exportedAt: new Date().toISOString(),
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `autonomousforge-export-${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
        AF.toast.success('Data exported');
    },

    clearCache() {
        localStorage.clear();
        AF.toast.success('Cache cleared');
        setTimeout(() => location.reload(), 500);
    },

    setAccentColor(color) {
        // Update CSS custom property
        document.documentElement.style.setProperty('--accent-color', color);
        AF.state.accentColor = color;
        localStorage.setItem('af_accent_color', color);
        this.renderTabContent();
    },

    async unload() {
        // Cleanup
    },
};