/**
 * AUTONOMOUSFORGE - Sidebar Component
 * Responsive navigation sidebar with mobile drawer support
 */

const Sidebar = (function() {
    let currentPage = 'dashboard';
    let isMobile = false;

    function init() {
        updateMobileState();
        window.addEventListener('resize', updateMobileState);
    }

    function updateMobileState() {
        isMobile = window.innerWidth < 1024;
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.toggle('mobile', isMobile);
        }
    }

    function render(activePage) {
        currentPage = activePage;

        const navigation = [
            { route: '/dashboard', icon: dashboardIcon, label: 'Dashboard', badge: null },
            { route: '/chat', icon: chatIcon, label: 'AI Assistant', badge: null },
            { route: '/agents', icon: agentsIcon, label: 'Agents', badge: '16,111' },
            { route: '/projects', icon: projectsIcon, label: 'Projects', badge: null },
            { route: '/settings', icon: settingsIcon, label: 'Settings', badge: null },
        ];

        return AF.utils.create('aside', {
            class: `sidebar ${isMobile ? 'mobile' : ''} fixed top-0 left-0 h-full z-50 bg-forge-950 border-r border-forge-800 transition-transform duration-300 ease-out`,
            role: 'navigation',
            'aria-label': 'Main navigation'
        }, [
            // Logo section
            AF.utils.create('div', { class: 'flex items-center justify-between h-14 px-4 border-b border-forge-800' }, [
                AF.utils.create('a', { href: '/dashboard', class: 'flex items-center gap-3' }, [
                    AF.utils.create('div', { class: 'w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center' }, [
                        AF.utils.create('svg', { class: 'w-5 h-5 text-white', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M13 10V3L4 14h7v7l9-11h-7z' }),
                        ]),
                    ]),
                    AF.utils.create('span', { class: 'font-bold text-forge-50 text-lg hidden lg:block' }, 'AUTONOMOUSFORGE'),
                ]),
                isMobile && AF.utils.create('button', {
                    class: 'btn btn-ghost btn-icon text-forge-400 hover:text-forge-50',
                    'aria-label': 'Close sidebar',
                    onclick: () => AF.ui.closeSidebar(),
                }, [
                    AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                        AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M6 18L18 6M6 6l12 12' }),
                    ]),
                ]),
            ]),

            // Navigation
            AF.utils.create('nav', { class: 'flex-1 p-4 space-y-1 overflow-y-auto', role: 'menu' },
                navigation.map(item => renderNavItem(item))
            ),

            // User section at bottom
            AF.utils.create('div', { class: 'p-4 border-t border-forge-800' }, [
                AF.utils.create('div', { class: 'flex items-center gap-3 mb-3' }, [
                    AF.utils.create('div', { class: 'w-10 h-10 rounded-full bg-forge-800 flex items-center justify-center' }, [
                        AF.utils.create('svg', { class: 'w-5 h-5 text-forge-400', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' }),
                        ]),
                    ]),
                    AF.utils.create('div', { class: 'flex-1 min-w-0' }, [
                        AF.utils.create('p', { class: 'text-sm font-medium text-forge-50 truncate' }, AF.auth.getUser()?.email || 'Owner'),
                        AF.utils.create('p', { class: 'text-xs text-forge-500 truncate' }, 'Master Administrator'),
                    ]),
                ]),
                AF.utils.create('div', { class: 'space-y-1' }, [
                    AF.utils.create('a', {
                        href: '/settings',
                        class: 'btn btn-ghost btn-sm w-full justify-start',
                        onclick: (e) => { e.preventDefault(); AF.router.navigate('/settings'); AF.ui.closeSidebar(); }
                    }, [
                        AF.utils.create('svg', { class: 'w-4 h-4 mr-2', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' }),
                            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z' }),
                        ]),
                        'Settings',
                    ]),
                    AF.utils.create('button', {
                        class: 'btn btn-ghost btn-sm w-full justify-start text-danger hover:text-danger-hover',
                        onclick: () => AF.auth.logout().then(() => AF.router.navigate('/login'))
                    }, [
                        AF.utils.create('svg', { class: 'w-4 h-4 mr-2', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1' }),
                        ]),
                        'Sign Out',
                    ]),
                ]),
            ]),
        ]);
    }

    function renderNavItem(item) {
        const isActive = currentPage === item.route;
        return AF.utils.create('a', {
            href: item.route,
            class: `nav-item flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                isActive
                    ? 'bg-forge-800 text-forge-50'
                    : 'text-forge-400 hover:text-forge-50 hover:bg-forge-800'
            }`,
            role: 'menuitem',
            'aria-current': isActive ? 'page' : undefined,
            onclick: (e) => { e.preventDefault(); AF.router.navigate(item.route); AF.ui.closeSidebar(); }
        }, [
            AF.utils.create('span', { class: `flex-shrink-0 w-5 h-5 ${isActive ? 'text-accent-500' : 'text-forge-400'}` }, item.icon),
            AF.utils.create('span', { class: 'flex-1 font-medium text-sm' }, item.label),
            item.badge && AF.utils.create('span', { class: 'badge badge-xs badge-accent ml-auto' }, item.badge),
        ]);
    }

    // Icon definitions
    function dashboardIcon() {
        return AF.utils.create('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', 'stroke-width': '2' }, [
            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' }),
        ]);
    }

    function chatIcon() {
        return AF.utils.create('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', 'stroke-width': '2' }, [
            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' }),
        ]);
    }

    function agentsIcon() {
        return AF.utils.create('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', 'stroke-width': '2' }, [
            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' }),
        ]);
    }

    function projectsIcon() {
        return AF.utils.create('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', 'stroke-width': '2' }, [
            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' }),
        ]);
    }

    function settingsIcon() {
        return AF.utils.create('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', 'stroke-width': '2' }, [
            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' }),
            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z' }),
        ]);
    }

    return { init, render };
})();

export default Sidebar;