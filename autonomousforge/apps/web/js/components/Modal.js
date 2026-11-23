/**
 * AUTONOMOUSFORGE - Modal Component
 * Reusable modal dialogs
 */

const Modal = {
    stack: [],

    open(content, options = {}) {
        const { size = 'md', closeOnOverlay = true, closeOnEscape = true, title } = options;
        const id = AF.utils.generateId();

        const sizeClasses = {
            sm: 'max-w-md',
            md: 'max-w-lg',
            lg: 'max-w-2xl',
            xl: 'max-w-4xl',
            full: 'max-w-full mx-4',
        };

        const overlay = AF.utils.create('div', {
            class: 'modal-overlay fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm',
            dataset: { id },
        }, [
            AF.utils.create('div', {
                class: `modal bg-forge-950 border border-forge-800 rounded-xl shadow-2xl w-full ${sizeClasses[size]} transform transition-all`,
                role: 'dialog',
                'aria-modal': 'true',
                'aria-labelledby': title ? `${id}-title` : undefined,
            }, content),
        ]);

        if (closeOnOverlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) this.close(id);
            });
        }

        const handleEscape = (e) => {
            if (e.key === 'Escape' && this.stack[this.stack.length - 1] === id) {
                this.close(id);
            }
        };

        if (closeOnEscape) {
            document.addEventListener('keydown', handleEscape);
        }

        overlay._cleanup = () => {
            document.removeEventListener('keydown', handleEscape);
        };

        document.body.appendChild(overlay);
        document.body.style.overflow = 'hidden';
        this.stack.push({ id, cleanup: overlay._cleanup });

        // Focus trap
        const focusable = overlay.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusable.length > 0) {
            focusable[0].focus();
        }

        return id;
    },

    close(id) {
        const index = this.stack.findIndex(item => item.id === id);
        if (index === -1) return;

        const item = this.stack[index];
        const overlay = document.querySelector(`.modal-overlay[data-id="${id}"]`);

        if (overlay) {
            overlay.style.animation = 'fadeIn 0.2s ease-in reverse';
            setTimeout(() => overlay.remove(), 200);
        }

        item.cleanup?.();
        this.stack.splice(index, 1);

        if (this.stack.length === 0) {
            document.body.style.overflow = '';
        }
    },

    closeAll() {
        [...this.stack].forEach(item => this.close(item.id));
    },

    // Pre-built modals
    confirm(message, title = 'Confirm', options = {}) {
        return new Promise((resolve) => {
            const content = AF.utils.create('div', {}, [
                AF.utils.create('div', { class: 'modal-header' }, [
                    AF.utils.create('h3', { class: 'modal-title', id: 'confirm-title' }, title),
                ]),
                AF.utils.create('div', { class: 'modal-body' }, [
                    AF.utils.create('p', {}, message),
                ]),
                AF.utils.create('div', { class: 'modal-footer' }, [
                    AF.utils.create('button', { class: 'btn btn-secondary', onclick: () => { this.close(id); resolve(false); } }, options.cancelText || 'Cancel'),
                    AF.utils.create('button', { class: 'btn btn-primary', onclick: () => { this.close(id); resolve(true); } }, options.confirmText || 'Confirm'),
                ]),
            ]);
            const id = this.open(content, { size: 'sm', ...options });
        });
    },

    alert(message, title = 'Alert', options = {}) {
        return new Promise((resolve) => {
            const content = AF.utils.create('div', {}, [
                AF.utils.create('div', { class: 'modal-header' }, [
                    AF.utils.create('h3', { class: 'modal-title' }, title),
                ]),
                AF.utils.create('div', { class: 'modal-body' }, [
                    AF.utils.create('p', {}, message),
                ]),
                AF.utils.create('div', { class: 'modal-footer' }, [
                    AF.utils.create('button', { class: 'btn btn-primary', onclick: () => { this.close(id); resolve(); } }, options.okText || 'OK'),
                ]),
            ]);
            const id = this.open(content, { size: 'sm', ...options });
        });
    },

    prompt(message, title = 'Prompt', defaultValue = '', options = {}) {
        return new Promise((resolve) => {
            const inputId = AF.utils.generateId();
            let inputEl = null;

            const content = AF.utils.create('div', {}, [
                AF.utils.create('div', { class: 'modal-header' }, [
                    AF.utils.create('h3', { class: 'modal-title' }, title),
                ]),
                AF.utils.create('div', { class: 'modal-body' }, [
                    AF.utils.create('p', {}, message),
                    AF.utils.create('input', {
                        type: 'text',
                        id: inputId,
                        class: 'form-input mt-3',
                        value: defaultValue,
                        placeholder: options.placeholder,
                    }),
                ]),
                AF.utils.create('div', { class: 'modal-footer' }, [
                    AF.utils.create('button', { class: 'btn btn-secondary', onclick: () => { this.close(id); resolve(null); } }, options.cancelText || 'Cancel'),
                    AF.utils.create('button', { class: 'btn btn-primary', onclick: () => { this.close(id); resolve(inputEl.value); } }, options.confirmText || 'OK'),
                ]),
            ]);
            const id = this.open(content, { size: 'sm', ...options });

            inputEl = document.getElementById(inputId);
            inputEl?.focus();
            inputEl?.select();
        });
    },

    // Form modal
    form({ title, fields, onSubmit, submitText = 'Save', cancelText = 'Cancel', size = 'md', initialData = {} }) {
        return new Promise((resolve) => {
            const formId = AF.utils.generateId();

            const content = AF.utils.create('div', {}, [
                AF.utils.create('div', { class: 'modal-header' }, [
                    AF.utils.create('h3', { class: 'modal-title' }, title),
                ]),
                AF.utils.create('form', { id: formId, class: 'modal-body space-y-4' }, [
                    ...fields.map(field => this.renderField(field, initialData[field.name])),
                ]),
                AF.utils.create('div', { class: 'modal-footer' }, [
                    AF.utils.create('button', { type: 'button', class: 'btn btn-secondary', onclick: () => { this.close(id); resolve(null); } }, cancelText),
                    AF.utils.create('button', { type: 'submit', class: 'btn btn-primary' }, submitText),
                ]),
            ]);

            const id = this.open(content, { size });

            const form = document.getElementById(formId);
            form?.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                const data = {};
                formData.forEach((value, key) => data[key] = value);

                const submitBtn = form.querySelector('button[type="submit"]');
                const originalText = submitBtn.textContent;
                submitBtn.disabled = true;
                submitBtn.textContent = 'Saving...';

                try {
                    const result = await onSubmit(data);
                    this.close(id);
                    resolve(result);
                } catch (error) {
                    AF.toast.error(error.message);
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                }
            });
        });
    },

    renderField(field, initialValue) {
        const { name, label, type = 'text', placeholder, required, options, rows = 3, helpText } = field;
        const value = initialValue !== undefined ? initialValue : (field.defaultValue || '');

        let inputEl;
        switch (type) {
            case 'textarea':
                inputEl = AF.utils.create('textarea', {
                    name,
                    id: name,
                    class: 'form-input',
                    placeholder: placeholder || '',
                    rows,
                    required: required || false,
                }, value);
                break;
            case 'select':
                inputEl = AF.utils.create('select', {
                    name,
                    id: name,
                    class: 'form-input',
                    required: required || false,
                }, [
                    AF.utils.create('option', { value: '' }, placeholder || 'Select...'),
                    ...(options || []).map(opt =>
                        AF.utils.create('option', { value: opt.value, selected: opt.value === value }, opt.label)
                    ),
                ]);
                break;
            case 'checkbox':
                return AF.utils.create('div', { class: 'form-group' }, [
                    AF.utils.create('label', { class: 'flex items-center gap-2 cursor-pointer' }, [
                        AF.utils.create('input', {
                            type: 'checkbox',
                            name,
                            id: name,
                            class: 'w-4 h-4 rounded border-border bg-forge-800 text-accent-500 focus:ring-accent-500',
                            checked: value,
                        }),
                        AF.utils.create('span', { class: 'text-sm text-forge-300' }, label),
                    ]),
                    helpText && AF.utils.create('p', { class: 'text-xs text-forge-500 mt-1 ml-6' }, helpText),
                ]);
            default:
                inputEl = AF.utils.create('input', {
                    type,
                    name,
                    id: name,
                    class: 'form-input',
                    placeholder: placeholder || '',
                    value,
                    required: required || false,
                });
        }

        return AF.utils.create('div', { class: 'form-group' }, [
            label && AF.utils.create('label', { class: 'form-label', for: name }, label),
            inputEl,
            helpText && AF.utils.create('p', { class: 'form-help' }, helpText),
        ]);
    },
};

// Make available globally
window.AF.Modal = Modal;

export default Modal;