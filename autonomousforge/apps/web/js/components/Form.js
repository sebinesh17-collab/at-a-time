/**
 * AUTONOMOUSFORGE - Form Components
 * Reusable form elements with validation
 */

const Form = {
    // Input field
    input({ name, label, type = 'text', placeholder, value = '', required, disabled, error, helpText, className = '', autocomplete }) {
        return AF.utils.create('div', { class: `form-group ${className}` }, [
            label && AF.utils.create('label', { class: 'form-label', for: name }, label),
            AF.utils.create('input', {
                type,
                name,
                id: name,
                class: `form-input ${error ? 'border-danger' : ''}`,
                placeholder: placeholder || '',
                value,
                required: required || false,
                disabled: disabled || false,
                autocomplete: autocomplete || 'off',
                'aria-invalid': error ? 'true' : 'false',
                'aria-describedby': error ? `${name}-error` : (helpText ? `${name}-help` : undefined),
            }),
            error && AF.utils.create('p', { id: `${name}-error`, class: 'form-error', role: 'alert' }, error),
            helpText && !error && AF.utils.create('p', { id: `${name}-help`, class: 'form-help' }, helpText),
        ]);
    },

    // Textarea
    textarea({ name, label, placeholder, value = '', required, disabled, error, helpText, rows = 4, className = '' }) {
        return AF.utils.create('div', { class: `form-group ${className}` }, [
            label && AF.utils.create('label', { class: 'form-label', for: name }, label),
            AF.utils.create('textarea', {
                name,
                id: name,
                class: `form-input ${error ? 'border-danger' : ''}`,
                placeholder: placeholder || '',
                required: required || false,
                disabled: disabled || false,
                rows,
                'aria-invalid': error ? 'true' : 'false',
                'aria-describedby': error ? `${name}-error` : (helpText ? `${name}-help` : undefined),
            }, value),
            error && AF.utils.create('p', { id: `${name}-error`, class: 'form-error', role: 'alert' }, error),
            helpText && !error && AF.utils.create('p', { id: `${name}-help`, class: 'form-help' }, helpText),
        ]);
    },

    // Select dropdown
    select({ name, label, placeholder, value = '', required, disabled, error, helpText, options = [], className = '' }) {
        return AF.utils.create('div', { class: `form-group ${className}` }, [
            label && AF.utils.create('label', { class: 'form-label', for: name }, label),
            AF.utils.create('select', {
                name,
                id: name,
                class: `form-input ${error ? 'border-danger' : ''}`,
                required: required || false,
                disabled: disabled || false,
                'aria-invalid': error ? 'true' : 'false',
                'aria-describedby': error ? `${name}-error` : (helpText ? `${name}-help` : undefined),
            }, [
                AF.utils.create('option', { value: '' }, placeholder || 'Select...'),
                ...options.map(opt =>
                    AF.utils.create('option', { value: opt.value, selected: opt.value === value }, opt.label)
                ),
            ]),
            error && AF.utils.create('p', { id: `${name}-error`, class: 'form-error', role: 'alert' }, error),
            helpText && !error && AF.utils.create('p', { id: `${name}-help`, class: 'form-help' }, helpText),
        ]);
    },

    // Checkbox
    checkbox({ name, label, checked = false, required, disabled, error, helpText, className = '' }) {
        const id = name + '-checkbox';
        return AF.utils.create('div', { class: `form-group ${className}` }, [
            AF.utils.create('label', { class: 'flex items-center gap-2 cursor-pointer', for: id }, [
                AF.utils.create('input', {
                    type: 'checkbox',
                    name,
                    id,
                    class: 'w-4 h-4 rounded border-border bg-forge-800 text-accent-500 focus:ring-accent-500',
                    checked,
                    required: required || false,
                    disabled: disabled || false,
                    'aria-invalid': error ? 'true' : 'false',
                }),
                AF.utils.create('span', { class: 'text-sm text-forge-300' }, label),
            ]),
            error && AF.utils.create('p', { id: `${name}-error`, class: 'form-error ml-6', role: 'alert' }, error),
            helpText && !error && AF.utils.create('p', { id: `${name}-help`, class: 'form-help ml-6' }, helpText),
        ]);
    },

    // Checkbox group
    checkboxGroup({ name, label, options = [], values = [], required, disabled, error, helpText, className = '' }) {
        return AF.utils.create('div', { class: `form-group ${className}` }, [
            label && AF.utils.create('fieldset', { class: 'space-y-2' }, [
                AF.utils.create('legend', { class: 'form-label' }, label),
                ...options.map(opt => AF.utils.create('label', { class: 'flex items-center gap-2 cursor-pointer' }, [
                    AF.utils.create('input', {
                        type: 'checkbox',
                        name,
                        value: opt.value,
                        class: 'w-4 h-4 rounded border-border bg-forge-800 text-accent-500 focus:ring-accent-500',
                        checked: values.includes(opt.value),
                        disabled: disabled || false,
                    }),
                    AF.utils.create('span', { class: 'text-sm text-forge-300' }, opt.label),
                ])),
            ]),
            error && AF.utils.create('p', { id: `${name}-error`, class: 'form-error', role: 'alert' }, error),
            helpText && !error && AF.utils.create('p', { id: `${name}-help`, class: 'form-help' }, helpText),
        ]);
    },

    // Radio group
    radioGroup({ name, label, options = [], value = '', required, disabled, error, helpText, inline = false, className = '' }) {
        return AF.utils.create('div', { class: `form-group ${className}` }, [
            label && AF.utils.create('fieldset', { class: inline ? 'flex flex-wrap gap-4' : 'space-y-2' }, [
                AF.utils.create('legend', { class: inline ? 'form-label mr-4' : 'form-label' }, label),
                ...options.map(opt => AF.utils.create('label', { class: inline ? 'flex items-center gap-2 cursor-pointer' : 'flex items-center gap-2 cursor-pointer' }, [
                    AF.utils.create('input', {
                        type: 'radio',
                        name,
                        value: opt.value,
                        class: 'w-4 h-4 border-border bg-forge-800 text-accent-500 focus:ring-accent-500',
                        checked: opt.value === value,
                        disabled: disabled || false,
                    }),
                    AF.utils.create('span', { class: 'text-sm text-forge-300' }, opt.label),
                ])),
            ]),
            error && AF.utils.create('p', { id: `${name}-error`, class: 'form-error', role: 'alert' }, error),
            helpText && !error && AF.utils.create('p', { id: `${name}-help`, class: 'form-help' }, helpText),
        ]);
    },

    // Switch/Toggle
    switch({ name, label, checked = false, required, disabled, error, helpText, className = '' }) {
        return AF.utils.create('div', { class: `form-group ${className}` }, [
            AF.utils.create('label', { class: 'flex items-center justify-between cursor-pointer', for: name }, [
                label && AF.utils.create('span', { class: 'text-sm font-medium text-forge-300' }, label),
                AF.utils.create('button', {
                    type: 'button',
                    role: 'switch',
                    name,
                    id: name,
                    class: `relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-accent-500 focus:ring-offset-2 focus:ring-offset-forge-950 ${checked ? 'bg-accent-500' : 'bg-forge-700'}`,
                    'aria-checked': checked,
                    disabled: disabled || false,
                    onclick: (e) => {
                        if (!disabled) {
                            e.target.click();
                        }
                    },
                }, [
                    AF.utils.create('span', {
                        class: `pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${checked ? 'translate-x-5' : 'translate-x-0'}`,
                    }),
                ]),
            ]),
            error && AF.utils.create('p', { id: `${name}-error`, class: 'form-error', role: 'alert' }, error),
            helpText && !error && AF.utils.create('p', { id: `${name}-help`, class: 'form-help' }, helpText),
        ]);
    },

    // File input
    file({ name, label, accept, multiple = false, required, disabled, error, helpText, className = '' }) {
        return AF.utils.create('div', { class: `form-group ${className}` }, [
            label && AF.utils.create('label', { class: 'form-label', for: name }, label),
            AF.utils.create('div', { class: 'relative' }, [
                AF.utils.create('input', {
                    type: 'file',
                    name,
                    id: name,
                    class: 'form-input file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-accent-500/20 file:text-accent-500 hover:file:bg-accent-500/30',
                    accept: accept || '',
                    multiple,
                    required: required || false,
                    disabled: disabled || false,
                    'aria-invalid': error ? 'true' : 'false',
                    'aria-describedby': error ? `${name}-error` : (helpText ? `${name}-help` : undefined),
                }),
            ]),
            error && AF.utils.create('p', { id: `${name}-error`, class: 'form-error', role: 'alert' }, error),
            helpText && !error && AF.utils.create('p', { id: `${name}-help`, class: 'form-help' }, helpText),
        ]);
    },

    // Hidden input
    hidden({ name, value }) {
        return AF.utils.create('input', { type: 'hidden', name, value: value || '' });
    },

    // Form actions (submit/cancel buttons)
    actions({ submitText = 'Save', cancelText = 'Cancel', onCancel, submitVariant = 'primary', cancelVariant = 'secondary', className = '' }) {
        return AF.utils.create('div', { class: `flex items-center justify-end gap-3 pt-4 border-t border-forge-800 ${className}` }, [
            onCancel && AF.utils.create('button', {
                type: 'button',
                class: `btn btn-${cancelVariant}`,
                onclick: onCancel,
            }, cancelText),
            AF.utils.create('button', {
                type: 'submit',
                class: `btn btn-${submitVariant}`,
            }, submitText),
        ]);
    },

    // Form row (for inline fields)
    row(...fields) {
        return AF.utils.create('div', { class: 'grid gap-4 md:grid-cols-2' }, fields);
    },

    // Full form builder
    build({ fields, onSubmit, initialData = {}, submitText = 'Submit', cancelText = 'Cancel', onCancel, className = '' }) {
        const formId = AF.utils.generateId();

        return AF.utils.create('form', { id: formId, class: `space-y-6 ${className}`, novalidate: true }, [
            ...fields.map(field => {
                if (field.type === 'row') {
                    return this.row(...field.fields.map(f => this[f.type]({ ...f, value: initialData[f.name] })));
                }
                return this[field.type]({ ...field, value: initialData[field.name] });
            }),
            this.actions({ submitText, cancelText, onCancel }),
            // Hidden fields for initial data not in fields
            ...Object.entries(initialData).filter(([key]) => !fields.some(f => f.name === key)).map(([key, value]) => this.hidden({ name: key, value })),
        ]);
    },

    // Get form data
    getData(form) {
        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => {
            if (data[key] !== undefined) {
                if (!Array.isArray(data[key])) data[key] = [data[key]];
                data[key].push(value);
            } else {
                data[key] = value;
            }
        });
        return data;
    },

    // Set form data
    setData(form, data) {
        Object.entries(data).forEach(([key, value]) => {
            const field = form.querySelector(`[name="${key}"]`);
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = Array.isArray(value) ? value.includes(field.value) : Boolean(value);
                } else if (field.type === 'radio') {
                    field.checked = field.value === value;
                } else if (field.tagName === 'SELECT' && field.multiple) {
                    Array.from(field.options).forEach(opt => opt.selected = value.includes(opt.value));
                } else {
                    field.value = value;
                }
            }
        });
    },

    // Validate form
    validate(form, rules = {}) {
        const errors = {};
        const data = this.getData(form);

        Object.entries(rules).forEach(([fieldName, rule]) => {
            const value = data[fieldName];
            const field = form.querySelector(`[name="${fieldName}"]`);

            if (rule.required && (value === undefined || value === '' || (Array.isArray(value) && value.length === 0))) {
                errors[fieldName] = rule.message || `${fieldName} is required`;
            } else if (value && rule.minLength && value.length < rule.minLength) {
                errors[fieldName] = rule.message || `Must be at least ${rule.minLength} characters`;
            } else if (value && rule.maxLength && value.length > rule.maxLength) {
                errors[fieldName] = rule.message || `Must be no more than ${rule.maxLength} characters`;
            } else if (value && rule.pattern && !rule.pattern.test(value)) {
                errors[fieldName] = rule.message || 'Invalid format';
            } else if (value && rule.custom && !rule.custom(value, data)) {
                errors[fieldName] = rule.message || 'Invalid value';
            }
        });

        // Display errors
        Object.entries(errors).forEach(([fieldName, message]) => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                const group = field.closest('.form-group');
                if (group) {
                    group.classList.add('has-error');
                    let errorEl = group.querySelector('.form-error');
                    if (!errorEl) {
                        errorEl = AF.utils.create('p', { class: 'form-error', role: 'alert' });
                        group.appendChild(errorEl);
                    }
                    errorEl.textContent = message;
                    field.setAttribute('aria-invalid', 'true');
                    field.setAttribute('aria-describedby', errorEl.id || `${fieldName}-error`);
                }
            }
        });

        // Clear errors for valid fields
        const allFields = form.querySelectorAll('[name]');
        allFields.forEach(field => {
            const fieldName = field.name;
            if (!errors[fieldName]) {
                const group = field.closest('.form-group');
                if (group) {
                    group.classList.remove('has-error');
                    const errorEl = group.querySelector('.form-error');
                    errorEl?.remove();
                    field.removeAttribute('aria-invalid');
                    field.removeAttribute('aria-describedby');
                }
            }
        });

        return { isValid: Object.keys(errors).length === 0, errors, data };
    },
};

export default Form;