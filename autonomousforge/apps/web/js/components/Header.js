/**
 * AUTONOMOUSFORGE - Header Component
 * Mobile-first responsive header with breadcrumbs and actions
 */

const Header = (function() {
    let currentPage = 'dashboard';
    let breadcrumbs = [];
    let actions = [];

    function render(pageName, pageBreadcrumbs = [], pageActions = []) {
        currentPage = pageName;
        breadcrumbs = pageBreadcrumbs;
        actions = pageActions;

        return AF.utils.create('header', {
            class: 'fixed top-0 left-0 right-0 h-14 bg-forge-950/95 backdrop-blur-sm border-b border-forge-800 z-40 flex items-center px-4 safe-top lg:hidden',
            role: 'banner'
        }, [
            // Sidebar toggle
            AF.utils.create('button', {
                class: 'btn btn-ghost btn-icon -ml-2 sidebar-toggle',
                'aria-label': 'Open menu',
                onclick: () => AF.ui.toggleSidebar(),
            }, [
                AF.utils.create('svg', { class: 'w-6 h-6', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                    AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 6h16M4 12h16M4 18h16' }),
                ]),
            ]),

            // Breadcrumbs / Title
            AF.utils.create('div', { class: 'flex-1 flex items-center gap-2 min-w-0' }, [
                breadcrumbs.length > 0 ? AF.utils.create('nav', { class: 'flex items-center gap-2 overflow-x-auto flex-nowrap pb-1', 'aria-label': 'Breadcrumb' }, [
                    AF.utils.create('a', {
                        href: '/dashboard',
                        class: 'btn btn-ghost btn-xs px-2 py-1 text-forge-400 hover:text-forge-50 whitespace-nowrap',
                        onclick: (e) => { e.preventDefault(); AF.router.navigate('/dashboard'); }
                    }, [
                        AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' }),
                        ]),
                    ]),
                    ...breadcrumbs.map((crumb, index) => [
                        AF.utils.create('svg', { class: 'w-3 h-3 text-forge-600 flex-shrink-0', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9 5l7 7-7 7' }),
                        ]),
                        index === breadcrumbs.length - 1
                            ? AF.utils.create('span', { class: 'text-sm font-medium text-forge-50 truncate max-w-[150px] whitespace-nowrap' }, crumb)
                            : AF.utils.create('a', {
                                href: crumb.href,
                                class: 'text-sm text-forge-400 hover:text-forge-50 truncate max-w-[100px] whitespace-nowrap',
                                onclick: crumb.onClick ? (e) => { e.preventDefault(); crumb.onClick(); } : undefined
                            }, crumb.label || crumb),
                    ]).flat(),
                ]) : AF.utils.create('h1', { class: 'text-lg font-semibold text-forge-50 truncate' }, getPageTitle(pageName)),
            ]),

            // Actions
            AF.utils.create('div', { class: 'flex items-center gap-1' }, [
                ...actions.map(action => renderAction(action)),
            ]),
        ]);
    }

    function getPageTitle(pageName) {
        const titles = {
            'dashboard': 'Dashboard',
            'chat': 'AI Assistant',
            'agents': 'Agents',
            'projects': 'Projects',
            'settings': 'Settings',
        };
        return titles[pageName] || pageName;
    }

    function renderAction(action) {
        return AF.utils.create('button', {
            class: `btn btn-ghost btn-icon ${action.variant || ''} ${action.class || ''}`,
            'aria-label': action.label,
            onclick: action.onClick,
            disabled: action.disabled,
        }, [
            action.icon ? action.icon() : defaultIcon(action.iconName),
        ]);
    }

    function defaultIcon(name) {
        const icons = {
            search: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' }),
            ]),
            add: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 4v16m8-8H4' }),
            ]),
            settings: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' }),
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z' }),
            ]),
            refresh: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' }),
            ]),
            filter: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z' }),
            ]),
            more: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z' }),
            ]),
        };
        return icons[name] || icons.more;
    }

    // Desktop header (shows in sidebar area on desktop)
    function renderDesktop(pageName, pageBreadcrumbs = [], pageActions = []) {
        return AF.utils.create('header', {
            class: 'lg:flex lg:fixed lg:top-0 lg:left-64 lg:right-0 lg:h-14 lg:z-40 lg:bg-forge-950/95 lg:backdrop-blur-sm lg:border-b lg:border-forge-800 flex items-center px-6 hidden',
            role: 'banner'
        }, [
            // Breadcrumbs
            pageBreadcrumbs.length > 0 && AF.utils.create('nav', { class: 'flex items-center gap-2 flex-1 overflow-x-auto', 'aria-label': 'Breadcrumb' }, [
                AF.utils.create('a', {
                    href: '/dashboard',
                    class: 'btn btn-ghost btn-sm px-3 py-1.5 text-forge-400 hover:text-forge-50 whitespace-nowrap',
                    onclick: (e) => { e.preventDefault(); AF.router.navigate('/dashboard'); }
                }, [
                    AF.utils.create('svg', { class: 'w-4 h-4 mr-1', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                        AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' }),
                    ]),
                    AF.utils.create('span', { class: 'hidden sm:inline' }, 'Dashboard'),
                ]),
                ...pageBreadcrumbs.map((crumb, index) => [
                    AF.utils.create('svg', { class: 'w-3 h-3 text-forge-600 flex-shrink-0', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                        AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9 5l7 7-7 7' }),
                    ]),
                    index === pageBreadcrumbs.length - 1
                        ? AF.utils.create('span', { class: 'text-sm font-medium text-forge-50 truncate max-w-[200px] whitespace-nowrap' }, crumb)
                        : AF.utils.create('a', {
                            href: crumb.href,
                            class: 'text-sm text-forge-400 hover:text-forge-50 truncate max-w-[120px] whitespace-nowrap',
                            onclick: crumb.onClick ? (e) => { e.preventDefault(); crumb.onClick(); } : undefined
                        }, crumb.label || crumb),
                ]).flat(),
            ]),

            // Actions
            AF.utils.create('div', { class: 'flex items-center gap-2' }, [
                ...pageActions.map(action => renderAction(action)),
            ]),
        ]);
    }

    return { render, renderDesktop };
})();

export default Header;