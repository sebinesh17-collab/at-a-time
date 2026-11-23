/**
 * AUTONOMOUSFORGE - Toast Notifications
 * Non-blocking notification system
 */

const Toast = {
    container: null,
    toasts: [],
    defaultDuration: 5000,

    init() {
        if (this.container) return;
        this.container = AF.utils.create('div', {
            id: 'toast-container',
            class: 'fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-full max-w-sm lg:max-w-md',
            'aria-live': 'polite',
            'aria-atomic': 'true',
        });
        document.body.appendChild(this.container);
    },

    show(message, options = {}) {
        this.init();

        const {
            type = 'info',
            title,
            duration = this.defaultDuration,
            action,
            dismissible = true,
            icon,
        } = options;

        const id = AF.utils.generateId();

        const typeStyles = {
            success: 'border-success/50 bg-success/10 text-success',
            error: 'border-danger/50 bg-danger/10 text-danger',
            warning: 'border-warning/50 bg-warning/10 text-warning',
            info: 'border-accent-500/50 bg-accent-500/10 text-accent-500',
        };

        const typeIcons = {
            success: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' }),
            ]),
            error: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z' }),
            ]),
            warning: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' }),
            ]),
            info: AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' }),
            }),
        };

        const toastEl = AF.utils.create('div', {
            class: `toast toast-${type} flex items-start gap-3 p-4 rounded-lg border shadow-lg animate-slide-up ${typeStyles[type]}`,
            role: 'alert',
            dataset: { id },
        }, [
            AF.utils.create('div', { class: 'flex-shrink-0 mt-0.5' }, icon || typeIcons[type]),
            AF.utils.create('div', { class: 'flex-1 min-w-0' }, [
                title && AF.utils.create('p', { class: 'font-semibold text-sm' }, title),
                AF.utils.create('p', { class: 'text-sm mt-1' }, message),
                action && AF.utils.create('button', {
                    class: 'btn btn-xs btn-primary mt-2',
                    onclick: () => { action.onClick(); this.dismiss(id); },
                }, action.label),
            ]),
            dismissible && AF.utils.create('button', {
                class: 'flex-shrink-0 text-forge-400 hover:text-forge-50 transition-colors',
                onclick: () => this.dismiss(id),
                'aria-label': 'Dismiss',
            }, [
                AF.utils.create('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                    AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M6 18L18 6M6 6l12 12' }),
                ]),
            ]),
        ]);

        this.container.appendChild(toastEl);
        this.toasts.push({ id, element: toastEl });

        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => this.dismiss(id), duration);
        }

        return id;
    },

    dismiss(id) {
        const index = this.toasts.findIndex(t => t.id === id);
        if (index === -1) return;

        const toast = this.toasts[index];
        toast.element.style.animation = 'slideInRight 0.2s ease-in reverse';
        setTimeout(() => {
            toast.element.remove();
            this.toasts.splice(index, 1);
        }, 200);
    },

    dismissAll() {
        [...this.toasts].forEach(t => this.dismiss(t.id));
    },

    // Convenience methods
    success(message, options = {}) {
        return this.show(message, { ...options, type: 'success' });
    },

    error(message, options = {}) {
        return this.show(message, { ...options, type: 'error' });
    },

    warning(message, options = {}) {
        return this.show(message, { ...options, type: 'warning' });
    },

    info(message, options = {}) {
        return this.show(message, { ...options, type: 'info' });
    },
};

// Make available globally
window.AF.Toast = Toast;

export default Toast;