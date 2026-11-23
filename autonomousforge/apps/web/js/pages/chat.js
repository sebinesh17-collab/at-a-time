/**
 * Chat Page - AI Assistant Interface
 */
export default {
    messages: [],
    currentModel: null,
    models: [],
    isLoading: false,
    abortController: null,

    async init(params = {}) {
        if (!AF.auth.isAuthenticated()) {
            AF.router.navigate(AF.CONFIG.ROUTES.LOGIN, true);
            return;
        }
        await this.loadModels();
        this.messages = [];
        this.renderMessages();
    },

    async loadModels() {
        try {
            const response = await AF.utils.get('/models');
            this.models = response.models || [];
            this.currentModel = this.models[0]?.id || null;
        } catch (error) {
            console.error('Failed to load models:', error);
            this.models = [];
        }
    },

    async sendMessage(content, options = {}) {
        if (this.isLoading || !content.trim()) return;

        const userMessage = {
            id: AF.utils.generateId(),
            role: 'user',
            content: content.trim(),
            timestamp: new Date().toISOString(),
            model: this.currentModel,
        };

        this.messages.push(userMessage);
        this.renderMessages();
        this.isLoading = true;

        // Create assistant message placeholder
        const assistantMessage = {
            id: AF.utils.generateId(),
            role: 'assistant',
            content: '',
            timestamp: new Date().toISOString(),
            model: this.currentModel,
            streaming: true,
        };
        this.messages.push(assistantMessage);
        this.renderMessages();

        this.abortController = new AbortController();

        try {
            const response = await AF.utils.post('/chat/completions', {
                model: this.currentModel,
                messages: this.messages.filter(m => !m.streaming).map(m => ({ role: m.role, content: m.content })),
                stream: true,
                temperature: 0.7,
                max_tokens: 4096,
            }, { signal: this.abortController.signal });

            // Handle streaming response
            if (response.body) {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.slice(6);
                            if (data === '[DONE]') continue;
                            try {
                                const parsed = JSON.parse(data);
                                const delta = parsed.choices?.[0]?.delta?.content || '';
                                if (delta) {
                                    assistantMessage.content += delta;
                                    this.renderMessages();
                                }
                            } catch (e) {
                                // Ignore parse errors
                            }
                        }
                    }
                }
            }

            assistantMessage.streaming = false;
            this.renderMessages();

        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Chat error:', error);
                assistantMessage.content = `Error: ${error.message}`;
                assistantMessage.streaming = false;
                this.renderMessages();
            }
        } finally {
            this.isLoading = false;
        }
    },

    stopGeneration() {
        if (this.abortController) {
            this.abortController.abort();
            this.abortController = null;
        }
        const streamingMsg = this.messages.find(m => m.streaming);
        if (streamingMsg) {
            streamingMsg.streaming = false;
            streamingMsg.content += '\n\n*[Generation stopped]*';
            this.renderMessages();
        }
        this.isLoading = false;
    },

    clearChat() {
        this.messages = [];
        this.renderMessages();
    },

    setModel(modelId) {
        this.currentModel = modelId;
        this.renderModelSelector();
    },

    render() {
        return AF.utils.create('div', { class: 'min-h-screen flex flex-col', id: 'chat-page' }, [
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
                    AF.utils.create('h1', { class: 'text-lg font-semibold text-forge-50' }, 'AI Chat'),
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
                    AF.utils.create('div', { class: 'p-3 border-t border-forge-800' }, [
                        AF.utils.create('button', { class: 'btn btn-secondary w-full justify-start', onclick: () => this.clearChat() }, [
                            AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' })]),
                            ' New Chat',
                        ]),
                    ]),
                ]),
            ]),

            // Sidebar overlay
            AF.utils.create('div', { class: 'fixed inset-0 z-40 bg-black/50 hidden lg:hidden sidebar-overlay', onclick: () => AF.ui.closeSidebar(), 'aria-hidden': 'true' }),

            // Main Content
            AF.utils.create('main', { class: 'flex-1 pt-14 lg:pt-0 lg:ml-64 min-h-screen flex flex-col', role: 'main' }, [
                // Model selector bar
                AF.utils.create('div', { class: 'border-b border-forge-800 bg-forge-950/50 px-4 py-2 lg:px-6' }, [
                    AF.utils.create('div', { class: 'flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3', id: 'model-selector-container' }, [
                        AF.utils.create('div', { class: 'flex items-center gap-3 flex-1' }, [
                            AF.utils.create('label', { class: 'text-sm text-forge-400 font-medium', for: 'model-select' }, 'Model:'),
                            AF.utils.create('select', {
                                id: 'model-select',
                                class: 'bg-forge-800 border border-forge-700 rounded-lg px-3 py-2 text-sm text-forge-100 focus:outline-none focus:ring-2 focus:ring-accent-500',
                                onchange: (e) => this.setModel(e.target.value),
                            }, this.models.map(m => AF.utils.create('option', { value: m.id }, m.name || m.id))),
                        ]),
                        AF.utils.create('div', { class: 'flex items-center gap-2' }, [
                            AF.utils.create('span', { class: 'text-xs text-forge-500', id: 'token-count' }, '0 tokens'),
                        ]),
                    ]),
                ]),

                // Messages area
                AF.utils.create('div', { class: 'flex-1 overflow-y-auto p-4 lg:p-6 space-y-6', id: 'messages-container', role: 'log', 'aria-live': 'polite' }, [
                    AF.utils.create('div', { id: 'messages-list' }),
                ]),

                // Input area
                AF.utils.create('div', { class: 'border-t border-forge-800 bg-forge-950/50 p-4 lg:p-6 safe-bottom' }, [
                    AF.utils.create('div', { class: 'flex gap-3' }, [
                        AF.utils.create('div', { class: 'flex-1 relative' }, [
                            AF.utils.create('textarea', {
                                id: 'chat-input',
                                class: 'w-full bg-forge-900 border border-forge-700 rounded-xl px-4 py-3 text-forge-100 placeholder-forge-500 focus:outline-none focus:ring-2 focus:ring-accent-500 resize-none',
                                rows: 1,
                                placeholder: 'Message AUTONOMOUSFORGE... (Shift+Enter for new line)',
                                onkeydown: (e) => this.handleInputKeydown(e),
                                oninput: (e) => this.autoResize(e.target),
                            }),
                            AF.utils.create('div', { class: 'absolute bottom-2 right-2 flex gap-1', id: 'input-actions' }, [
                                AF.utils.create('button', {
                                    type: 'button',
                                    class: 'btn btn-ghost btn-sm',
                                    onclick: () => AF.router.navigate(AF.CONFIG.ROUTES.FILES),
                                    'aria-label': 'Attach files',
                                }, [
                                    AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13' })]),
                                ]),
                            ]),
                        ]),
                        AF.utils.create('button', {
                            id: 'send-btn',
                            type: 'button',
                            class: 'btn btn-primary p-3 flex-shrink-0',
                            onclick: () => this.handleSend(),
                            disabled: this.isLoading,
                            'aria-label': this.isLoading ? 'Stop generation' : 'Send message',
                        }, [
                            AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', id: 'send-icon' }, [
                                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 19l9 2-9-18-9 18 9-2zm0 0v-8' }),
                            ]),
                        ]),
                    ]),
                    AF.utils.create('p', { class: 'text-xs text-forge-500 mt-2 text-center' }, 'Press Enter to send, Shift+Enter for new line. Your data never leaves your infrastructure.'),
                ]),
            ]),
        ]);
    },

    renderMessages() {
        const container = document.getElementById('messages-list');
        if (!container) return;

        container.innerHTML = '';

        if (this.messages.length === 0) {
            container.appendChild(AF.utils.create('div', { class: 'flex flex-col items-center justify-center h-64 text-forge-500' }, [
                AF.utils.create('svg', { class: 'w-16 h-16 mb-4 text-forge-700', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '1.5', d: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' })]),
                AF.utils.create('h3', { class: 'text-lg font-medium mb-2' }, 'Start a conversation'),
                AF.utils.create('p', { class: 'text-sm text-center max-w-xs' }, 'Ask questions, write code, analyze files, or delegate tasks to your agent swarm.'),
            ]));
            return;
        }

        this.messages.forEach(msg => {
            container.appendChild(this.renderMessage(msg));
        });

        // Auto-scroll to bottom
        container.scrollTop = container.scrollHeight;
    },

    renderMessage(msg) {
        const isUser = msg.role === 'user';
        const isStreaming = msg.streaming;

        return AF.utils.create('div', {
            class: `flex gap-3 ${isUser ? 'flex-row-reverse' : ''} animate-slide-up`,
            'data-message-id': msg.id,
        }, [
            // Avatar
            AF.utils.create('div', {
                class: `w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${isUser ? 'bg-forge-800 border border-forge-700' : 'bg-accent-500/10 border border-accent-500/20'}`,
            }, [
                isUser
                    ? AF.utils.create('span', { class: 'text-xs font-mono text-forge-400' }, 'U')
                    : AF.utils.create('svg', { class: 'w-5 h-5 text-accent-500', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                        AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M13 10V3L4 14h7v7l9-11h-7z' }),
                    ]),
            ]),

            // Message content
            AF.utils.create('div', {
                class: `flex-1 min-w-0 ${isUser ? 'text-right' : ''}`,
            }, [
                AF.utils.create('div', {
                    class: `inline-block max-w-[85%] lg:max-w-[70%] ${isUser ? 'bg-forge-800 border border-forge-700' : 'bg-forge-900 border border-forge-800'} rounded-2xl px-4 py-3`,
                }, [
                    AF.utils.create('div', {
                        class: 'prose prose-invert max-w-none text-forge-100',
                        innerHTML: this.formatMessage(msg.content),
                    }),
                    isStreaming && AF.utils.create('span', { class: 'inline-block w-2 h-4 bg-accent-500 animate-pulse ml-1 align-bottom' }),
                ]),
                AF.utils.create('div', { class: 'flex items-center gap-2 mt-1.5', style: isUser ? 'justify-flex-end' : '' }, [
                    AF.utils.create('span', { class: 'text-xs text-forge-500' }, AF.utils.formatTime(msg.timestamp)),
                    AF.utils.create('span', { class: 'text-xs text-forge-600 px-1.5 py-0.5 rounded bg-forge-800' }, msg.model || 'default'),
                    !isUser && AF.utils.create('button', {
                        class: 'btn btn-ghost btn-xs text-forge-500 hover:text-forge-300',
                        onclick: () => AF.utils.copyToClipboard(msg.content),
                        'aria-label': 'Copy message',
                    }, [
                        AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z' })]),
                    ]),
                ]),
            ]),
        ]);
    },

    formatMessage(content) {
        // Simple markdown-like formatting
        return AF.utils.escapeHtml(content)
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/`(.+?)`/g, '<code class="bg-forge-800 px-1.5 py-0.5 rounded text-accent-400 font-mono text-sm">$1</code>')
            .replace(/\n/g, '<br>')
            .replace(/```(\w+)?\n([\s\S]+?)```/g, '<pre class="bg-forge-900 border border-forge-700 rounded-lg p-4 overflow-x-auto my-2"><code class="font-mono text-sm">$2</code></pre>');
    },

    handleInputKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.handleSend();
        }
    },

    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    },

    handleSend() {
        const input = document.getElementById('chat-input');
        if (!input || !input.value.trim()) return;

        if (this.isLoading) {
            this.stopGeneration();
            return;
        }

        const content = input.value;
        input.value = '';
        input.style.height = 'auto';
        this.sendMessage(content);
    },

    renderModelSelector() {
        const select = document.getElementById('model-select');
        if (select) {
            select.value = this.currentModel || '';
        }
    },

    navItems = [
        { page: 'dashboard', label: 'Dashboard', route: AF.CONFIG.ROUTES.DASHBOARD, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' })]) },
        { page: 'chat', label: 'AI Chat', route: AF.CONFIG.ROUTES.CHAT, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' })]), active: true },
        { page: 'agents', label: 'Agent Center', route: AF.CONFIG.ROUTES.AGENTS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' })]) },
        { page: 'projects', label: 'Projects', route: AF.CONFIG.ROUTES.PROJECTS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z' })]) },
        { page: 'settings', label: 'Settings', route: AF.CONFIG.ROUTES.SETTINGS, icon: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' })]) },
    ],

    mount() {
        this.updateActiveNav();
        this.renderModelSelector();

        // Focus input
        setTimeout(() => {
            const input = document.getElementById('chat-input');
            if (input) input.focus();
        }, 100);
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
        this.stopGeneration();
    },
};