/**
 * AUTONOMOUSFORGE - Card Components
 * Reusable card layouts for consistent UI
 */

const Card = {
    // Basic card
    create(content, options = {}) {
        const { className = '', header, footer, padded = true } = options;
        return AF.utils.create('div', { class: `card ${className}` }, [
            header && AF.utils.create('div', { class: 'card-header' }, header),
            AF.utils.create('div', { class: padded ? 'card-body' : 'p-0' }, content),
            footer && AF.utils.create('div', { class: 'card-footer' }, footer),
        ]);
    },

    // Card with header actions
    withActions(content, { title, subtitle, actions = [], ...options } = {}) {
        const header = AF.utils.create('div', { class: 'flex items-center justify-between' }, [
            AF.utils.create('div', {}, [
                title && AF.utils.create('h3', { class: 'text-lg font-semibold text-forge-50' }, title),
                subtitle && AF.utils.create('p', { class: 'text-sm text-forge-400 mt-0.5' }, subtitle),
            ]),
            actions.length > 0 && AF.utils.create('div', { class: 'flex items-center gap-2' }, actions),
        ]);
        return this.create(content, { ...options, header });
    },

    // Stats card
    stat({ label, value, change, trend = 'neutral', icon, iconBg = 'purple' }) {
        const trendColors = {
            up: 'text-success',
            down: 'text-danger',
            neutral: 'text-muted',
        };
        const trendIcons = {
            up: AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M5 10l7-7m0 0l7 7m-7-7v18' }),
            ]),
            down: AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M19 14l-7 7m0 0l-7-7m7 7V3' }),
            ]),
            neutral: AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M5 12h14' }),
            ]),
        };

        const iconColors = {
            purple: 'bg-purple-600/20 text-purple-400',
            blue: 'bg-blue-600/20 text-blue-400',
            green: 'bg-green-600/20 text-green-400',
            orange: 'bg-orange-600/20 text-orange-400',
            red: 'bg-red-600/20 text-red-400',
            pink: 'bg-pink-600/20 text-pink-400',
        };

        return AF.utils.create('div', { class: 'card' }, [
            AF.utils.create('div', { class: 'card-body' }, [
                AF.utils.create('div', { class: 'flex items-center justify-between' }, [
                    AF.utils.create('div', {}, [
                        AF.utils.create('p', { class: 'text-sm font-medium text-forge-400' }, label),
                        AF.utils.create('p', { class: 'text-3xl font-bold text-forge-50 mt-1' }, value),
                    ]),
                    icon && AF.utils.create('div', { class: `w-12 h-12 rounded-xl flex items-center justify-center ${iconColors[iconBg] || iconColors.purple}` }, [
                        typeof icon === 'function' ? icon() : icon,
                    ]),
                ]),
                change !== undefined && AF.utils.create('div', { class: `flex items-center gap-1 mt-3 ${trendColors[trend]}` }, [
                    trendIcons[trend],
                    AF.utils.create('span', { class: 'text-sm font-medium' }, change),
                ]),
            ]),
        ]);
    },

    // Agent card
    agent(agent, options = {}) {
        const { onClick, showStatus = true, showActions = true } = options;

        const levelColors = {
            0: 'bg-purple-600 text-white',
            1: 'bg-blue-600 text-white',
            2: 'bg-green-600 text-white',
            3: 'bg-orange-600 text-white',
            4: 'bg-gray-600 text-white',
        };

        const levelNames = {
            0: 'Master',
            1: 'Principal',
            2: 'Head',
            3: 'Team Lead',
            4: 'Worker',
        };

        const statusColors = {
            active: 'bg-success',
            idle: 'bg-warning',
            paused: 'bg-muted',
            error: 'bg-danger',
            offline: 'bg-border',
        };

        const statusLabels = {
            active: 'Active',
            idle: 'Idle',
            paused: 'Paused',
            error: 'Error',
            offline: 'Offline',
        };

        return AF.utils.create('div', {
            class: `card group hover:border-accent-500/50 transition-colors cursor-pointer ${onClick ? '' : 'cursor-default'}`,
            onclick: onClick ? (e) => onClick(e, agent) : undefined,
        }, [
            AF.utils.create('div', { class: 'card-body' }, [
                AF.utils.create('div', { class: 'flex items-start gap-4' }, [
                    // Avatar/Icon
                    AF.utils.create('div', { class: 'flex-shrink-0' }, [
                        AF.utils.create('div', { class: `w-12 h-12 rounded-xl flex items-center justify-center ${levelColors[agent.level] || levelColors[4]}` }, [
                            AF.utils.create('svg', { class: 'w-6 h-6', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: getAgentIcon(agent.level) }),
                            ]),
                        ]),
                    ]),
                    // Info
                    AF.utils.create('div', { class: 'flex-1 min-w-0' }, [
                        AF.utils.create('div', { class: 'flex items-center gap-2' }, [
                            AF.utils.create('h4', { class: 'font-semibold text-forge-50 truncate' }, agent.name),
                            AF.utils.create('span', { class: `badge badge-xs ${levelColors[agent.level] || levelColors[4]}` }, levelNames[agent.level] || 'Unknown'),
                        ]),
                        AF.utils.create('p', { class: 'text-sm text-forge-400 truncate mt-0.5' }, agent.id),
                        AF.utils.create('p', { class: 'text-xs text-forge-500 truncate mt-1' }, agent.department),
                        showStatus && AF.utils.create('div', { class: 'flex items-center gap-2 mt-2' }, [
                            AF.utils.create('span', { class: `w-2 h-2 rounded-full ${statusColors[agent.status] || statusColors.offline}` }),
                            AF.utils.create('span', { class: 'text-xs text-forge-400' }, statusLabels[agent.status] || 'Unknown'),
                            agent.current_task_id && AF.utils.create('span', { class: 'text-xs text-accent-500 ml-2' }, 'Working...'),
                        ]),
                    ]),
                    // Actions
                    showActions && AF.utils.create('div', { class: 'flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity' }, [
                        AF.utils.create('button', {
                            class: 'btn btn-ghost btn-icon btn-sm text-forge-400 hover:text-forge-50',
                            'aria-label': 'View agent details',
                            onclick: (e) => { e.stopPropagation(); onClick?.(e, agent); }
                        }, [
                            AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z' }),
                                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z' }),
                            ]),
                        ]),
                    ]),
                ]),
            ]),
        ]);
    },

    // Project card
    project(project, options = {}) {
        const { onClick } = options;

        const statusColors = {
            planning: 'bg-blue-600/20 text-blue-400 border-blue-600/30',
            active: 'bg-green-600/20 text-green-400 border-green-600/30',
            review: 'bg-purple-600/20 text-purple-400 border-purple-600/30',
            completed: 'bg-gray-600/20 text-gray-400 border-gray-600/30',
            archived: 'bg-border text-muted border-border',
        };

        const progress = project.progress || 0;

        return AF.utils.create('div', {
            class: `card group hover:border-accent-500/50 transition-colors cursor-pointer ${onClick ? '' : 'cursor-default'}`,
            onclick: onClick ? (e) => onClick(e, project) : undefined,
        }, [
            AF.utils.create('div', { class: 'card-body' }, [
                AF.utils.create('div', { class: 'flex items-start justify-between gap-4' }, [
                    AF.utils.create('div', { class: 'flex-1 min-w-0' }, [
                        AF.utils.create('div', { class: 'flex items-center gap-2 flex-wrap' }, [
                            AF.utils.create('h4', { class: 'font-semibold text-forge-50 truncate' }, project.name),
                            AF.utils.create('span', { class: `badge badge-xs ${statusColors[project.status] || statusColors.planning}` }, project.status || 'Planning'),
                        ]),
                        project.description && AF.utils.create('p', { class: 'text-sm text-forge-400 mt-1 line-clamp-2' }, project.description),
                        AF.utils.create('div', { class: 'flex items-center gap-4 mt-3 text-xs text-forge-500' }, [
                            project.owner && AF.utils.create('span', {}, [
                                AF.utils.create('svg', { class: 'w-3 h-3 inline mr-1', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                                    AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' }),
                                ]),
                                project.owner,
                            ]),
                            project.updated_at && AF.utils.create('span', {}, [
                                AF.utils.create('svg', { class: 'w-3 h-3 inline mr-1', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                                    AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' }),
                                ]),
                                AF.utils.formatRelative(project.updated_at),
                            ]),
                        ]),
                    ]),
                ]),
                // Progress bar
                AF.utils.create('div', { class: 'mt-4' }, [
                    AF.utils.create('div', { class: 'flex items-center justify-between text-xs mb-1' }, [
                        AF.utils.create('span', { class: 'text-forge-400' }, 'Progress'),
                        AF.utils.create('span', { class: 'font-medium text-forge-50' }, `${Math.round(progress)}%`),
                    ]),
                    AF.utils.create('div', { class: 'w-full h-2 bg-forge-800 rounded-full overflow-hidden' }, [
                        AF.utils.create('div', {
                            class: 'h-full bg-gradient-to-r from-purple-600 to-pink-600 rounded-full transition-all duration-500',
                            style: `width: ${progress}%`,
                        }),
                    ]),
                ]),
            ]),
        ]);
    },

    // Task card
    task(task, options = {}) {
        const { onClick, compact = false } = options;

        const priorityColors = {
            critical: 'bg-danger/20 text-danger border-danger/30',
            high: 'bg-orange-600/20 text-orange-400 border-orange-600/30',
            medium: 'bg-blue-600/20 text-blue-400 border-blue-600/30',
            low: 'bg-muted/20 text-muted border-muted/30',
        };

        const statusColors = {
            todo: 'bg-border text-muted',
            in_progress: 'bg-blue-600/20 text-blue-400',
            review: 'bg-purple-600/20 text-purple-400',
            done: 'bg-success/20 text-success',
            blocked: 'bg-danger/20 text-danger',
        };

        return AF.utils.create('div', {
            class: `card group hover:border-accent-500/50 transition-colors ${compact ? 'p-3' : ''}`,
            onclick: onClick ? (e) => onClick(e, task) : undefined,
        }, [
            AF.utils.create('div', { class: compact ? 'flex items-center gap-3' : 'card-body' }, [
                AF.utils.create('div', { class: 'flex-1 min-w-0' }, [
                    AF.utils.create('div', { class: 'flex items-center gap-2 flex-wrap' }, [
                        AF.utils.create('h4', { class: `font-semibold text-forge-50 truncate ${compact ? 'text-sm' : ''}` }, task.title),
                        task.priority && AF.utils.create('span', { class: `badge badge-xs ${priorityColors[task.priority] || priorityColors.medium}` }, task.priority),
                        task.status && AF.utils.create('span', { class: `badge badge-xs ${statusColors[task.status] || statusColors.todo}` }, task.status),
                    ]),
                    !compact && task.description && AF.utils.create('p', { class: 'text-sm text-forge-400 mt-1 line-clamp-2' }, task.description),
                    !compact && AF.utils.create('div', { class: 'flex items-center gap-4 mt-3 text-xs text-forge-500' }, [
                        task.assignee && AF.utils.create('span', {}, [
                            AF.utils.create('svg', { class: 'w-3 h-3 inline mr-1', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' }),
                            ]),
                            task.assignee,
                        ]),
                        task.due_date && AF.utils.create('span', { class: task.due_date < new Date().toISOString() ? 'text-danger' : '' }, [
                            AF.utils.create('svg', { class: 'w-3 h-3 inline mr-1', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' }),
                            ]),
                            AF.utils.formatDate(task.due_date),
                        ]),
                    ]),
                ]),
            ]),
        ]);
    },
};

// Helper function for agent icons by level
function getAgentIcon(level) {
    const icons = {
        0: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
        1: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
        2: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z',
        3: 'M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z',
        4: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
    };
    return icons[level] || icons[4];
}

export default Card;