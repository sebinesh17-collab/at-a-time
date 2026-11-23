/**
 * Login Page
 */
export default {
    async init() {
        // Check if already authenticated
        if (AF.auth.isAuthenticated()) {
            AF.router.navigate(AF.CONFIG.ROUTES.DASHBOARD, true);
            return;
        }

        // Check if setup is complete
        try {
            const setup = await AF.utils.get('/auth/setup/status');
            if (!setup.setup_complete) {
                AF.router.navigate(AF.CONFIG.ROUTES.SETUP, true);
                return;
            }
        } catch {
            // If setup check fails, stay on login
        }
    },

    render() {
        const container = AF.utils.create('div', { class: 'min-h-screen flex items-center justify-center p-4 safe-top safe-bottom' }, [
            AF.utils.create('div', { class: 'w-full max-w-md animate-slide-up' }, [
                // Logo/Brand
                AF.utils.create('div', { class: 'text-center mb-10' }, [
                    AF.utils.create('div', { class: 'inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-forge-800 border border-forge-700 mb-6' }, [
                        AF.utils.create('svg', {
                            class: 'w-10 h-10 text-accent-500',
                            fill: 'none',
                            stroke: 'currentColor',
                            viewBox: '0 0 24 24',
                        }, [
                            AF.utils.create('path', {
                                'stroke-linecap': 'round',
                                'stroke-linejoin': 'round',
                                'stroke-width': '2',
                                d: 'M13 10V3L4 14h7v7l9-11h-7z',
                            }),
                        ]),
                    ]),
                    AF.utils.create('h1', { class: 'text-3xl font-bold text-forge-50 mb-2' }, 'AUTONOMOUSFORGE'),
                    AF.utils.create('p', { class: 'text-forge-400' }, 'Private Autonomous Engineering OS'),
                ]),

                // Login Form Card
                AF.utils.create('div', { class: 'card' }, [
                    AF.utils.create('div', { class: 'card-body' }, [
                        AF.utils.create('h2', { class: 'text-xl font-semibold mb-6 text-center' }, 'Sign In'),

                        AF.utils.create('form', { id: 'login-form', class: 'space-y-5' }, [
                            AF.utils.create('div', { class: 'form-group' }, [
                                AF.utils.create('label', { class: 'form-label', for: 'email' }, 'Email'),
                                AF.utils.create('input', {
                                    type: 'email',
                                    id: 'email',
                                    name: 'email',
                                    class: 'form-input',
                                    placeholder: 'owner@autonomousforge.local',
                                    autocomplete: 'email',
                                    required: true,
                                    autofocus: true,
                                }),
                            ]),

                            AF.utils.create('div', { class: 'form-group' }, [
                                AF.utils.create('div', { class: 'flex justify-between' }, [
                                    AF.utils.create('label', { class: 'form-label', for: 'password' }, 'Password'),
                                    AF.utils.create('a', { href: '#', class: 'text-sm text-accent-500 hover:underline', id: 'forgot-password' }, 'Forgot?'),
                                ]),
                                AF.utils.create('div', { class: 'relative' }, [
                                    AF.utils.create('input', {
                                        type: 'password',
                                        id: 'password',
                                        name: 'password',
                                        class: 'form-input pr-12',
                                        placeholder: '••••••••',
                                        autocomplete: 'current-password',
                                        required: true,
                                    }),
                                    AF.utils.create('button', {
                                        type: 'button',
                                        id: 'toggle-password',
                                        class: 'absolute right-3 top-1/2 -translate-y-1/2 text-forge-400 hover:text-forge-200',
                                        'aria-label': 'Toggle password visibility',
                                    }, '👁'),
                                ]),
                            ]),

                            AF.utils.create('div', { class: 'flex items-center justify-between' }, [
                                AF.utils.create('label', { class: 'flex items-center gap-2 cursor-pointer' }, [
                                    AF.utils.create('input', {
                                        type: 'checkbox',
                                        id: 'remember',
                                        name: 'remember_me',
                                        class: 'w-4 h-4 rounded border-forge-600 bg-forge-800 text-accent-500 focus:ring-accent-500',
                                    }),
                                    AF.utils.create('span', { class: 'text-sm text-forge-300' }, 'Remember me'),
                                ]),
                            ]),

                            AF.utils.create('button', {
                                type: 'submit',
                                class: 'btn btn-primary btn-block btn-lg mt-2',
                                id: 'login-btn',
                            }, [
                                AF.utils.create('span', { id: 'login-btn-text' }, 'Sign In'),
                                AF.utils.create('span', { id: 'login-btn-loading', class: 'hidden flex items-center gap-2' }, [
                                    AF.utils.create('span', { class: 'spinner spinner-sm' }),
                                    'Signing in...',
                                ]),
                            ]),

                            AF.utils.create('p', { id: 'login-error', class: 'text-center text-danger text-sm hidden' }),
                        ]),
                    ]),
                ]),

                // Footer info
                AF.utils.create('div', { class: 'text-center mt-6 text-forge-500 text-sm' }, [
                    AF.utils.create('p', {}, 'Single-owner private platform'),
                    AF.utils.create('p', {}, 'v1.0.0 · Secure access only'),
                ]),
            ]),
        ]);

        return container;
    },

    mount() {
        const form = document.getElementById('login-form');
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        const togglePassword = document.getElementById('toggle-password');
        const loginBtn = document.getElementById('login-btn');
        const loginBtnText = document.getElementById('login-btn-text');
        const loginBtnLoading = document.getElementById('login-btn-loading');
        const errorEl = document.getElementById('login-error');

        // Toggle password visibility
        togglePassword.addEventListener('click', () => {
            const type = passwordInput.type === 'password' ? 'text' : 'password';
            passwordInput.type = type;
            togglePassword.textContent = type === 'password' ? '👁' : '🙈';
        });

        // Form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = emailInput.value.trim();
            const password = passwordInput.value;
            const rememberMe = document.getElementById('remember').checked;

            if (!email || !password) {
                showError('Please enter both email and password');
                return;
            }

            setLoading(true);
            hideError();

            try {
                const result = await AF.auth.login(email, password, rememberMe);

                if (result.requires2fa) {
                    // Show 2FA modal
                    show2FAModal(result.email);
                } else {
                    AF.toast.success('Welcome back!');
                    AF.router.navigate(AF.CONFIG.ROUTES.DASHBOARD);
                }
            } catch (error) {
                showError(error.message || 'Login failed. Please check your credentials.');
            } finally {
                setLoading(false);
            }
        });

        function setLoading(loading) {
            loginBtn.disabled = loading;
            loginBtnText.classList.toggle('hidden', loading);
            loginBtnLoading.classList.toggle('hidden', !loading);
        }

        function showError(message) {
            errorEl.textContent = message;
            errorEl.classList.remove('hidden');
            emailInput.classList.add('border-danger');
            passwordInput.classList.add('border-danger');
        }

        function hideError() {
            errorEl.classList.add('hidden');
            emailInput.classList.remove('border-danger');
            passwordInput.classList.remove('border-danger');
        }

        function show2FAModal(email) {
            const content = AF.utils.create('div', {}, [
                AF.utils.create('div', { class: 'modal-header' }, [
                    AF.utils.create('h3', { class: 'modal-title' }, 'Two-Factor Authentication'),
                ]),
                AF.utils.create('div', { class: 'modal-body' }, [
                    AF.utils.create('p', { class: 'text-forge-300 mb-4' }, 'Enter the 6-digit code from your authenticator app'),
                    AF.utils.create('div', { class: 'flex gap-2 justify-center mb-4' }, [
                        ...Array.from({ length: 6 }, (_, i) => AF.utils.create('input', {
                            type: 'text',
                            maxlength: '1',
                            class: 'w-10 h-12 text-center text-2xl font-mono form-input',
                            'data-index': i,
                            inputmode: 'numeric',
                            pattern: '[0-9]*',
                            autocomplete: 'one-time-code',
                        })),
                    ]),
                    AF.utils.create('p', { id: '2fa-error', class: 'text-center text-danger text-sm hidden' }),
                ]),
                AF.utils.create('div', { class: 'modal-footer' }, [
                    AF.utils.create('button', { class: 'btn btn-secondary', onclick: 'AF.modal.closeAll()' }, 'Cancel'),
                    AF.utils.create('button', { class: 'btn btn-primary', id: '2fa-submit' }, 'Verify'),
                ]),
            ]);

            AF.modal.open(content);

            // Handle 2FA input
            const inputs = document.querySelectorAll('[data-index]');
            inputs.forEach((input, i) => {
                input.addEventListener('input', (e) => {
                    if (e.target.value && i < 5) inputs[i + 1].focus();
                });
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Backspace' && !e.target.value && i > 0) inputs[i - 1].focus();
                });
            });

            document.getElementById('2fa-submit').addEventListener('click', async () => {
                const code = Array.from(inputs).map(i => i.value).join('');
                if (code.length !== 6) {
                    document.getElementById('2fa-error').textContent = 'Please enter all 6 digits';
                    document.getElementById('2fa-error').classList.remove('hidden');
                    return;
                }

                try {
                    await AF.auth.login2fa(email, code);
                    AF.modal.closeAll();
                    AF.toast.success('Welcome back!');
                    AF.router.navigate(AF.CONFIG.ROUTES.DASHBOARD);
                } catch (error) {
                    document.getElementById('2fa-error').textContent = error.message || 'Invalid code';
                    document.getElementById('2fa-error').classList.remove('hidden');
                    inputs.forEach(i => i.value = '');
                    inputs[0].focus();
                }
            });

            inputs[0].focus();
        }
    },
};