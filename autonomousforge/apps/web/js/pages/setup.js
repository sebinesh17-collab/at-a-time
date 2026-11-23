/**
 * First-time Owner Setup Page
 */
export default {
    async init() {
        const setup = await AF.utils.get('/auth/setup/status');
        if (setup.setup_complete) {
            AF.router.navigate(AF.CONFIG.ROUTES.LOGIN, true);
            return;
        }
    },

    render() {
        return AF.utils.create('div', { class: 'min-h-screen flex items-center justify-center p-4 safe-top safe-bottom' }, [
            AF.utils.create('div', { class: 'w-full max-w-xl animate-slide-up' }, [
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
                    AF.utils.create('p', { class: 'text-forge-400 mb-1' }, 'Private Autonomous Engineering OS'),
                    AF.utils.create('p', { class: 'text-forge-500 text-sm mt-2' }, 'Initial Owner Setup'),
                ]),

                // Progress indicator
                AF.utils.create('div', { class: 'mb-8' }, [
                    AF.utils.create('div', { class: 'flex items-center justify-between mb-2' }, [
                        AF.utils.create('span', { class: 'text-sm font-medium text-forge-300' }, 'Step 1 of 2'),
                        AF.utils.create('span', { class: 'text-sm text-forge-500', id: 'progress-text' }, 'Account Details'),
                    ]),
                    AF.utils.create('div', { class: 'h-2 bg-forge-800 rounded-full overflow-hidden' }, [
                        AF.utils.create('div', {
                            class: 'h-full bg-accent-500 transition-all duration-300',
                            style: 'width: 50%',
                            id: 'progress-bar',
                        }),
                    ]),
                ]),

                // Setup Form Card
                AF.utils.create('div', { class: 'card', id: 'setup-card' }, [
                    AF.utils.create('div', { class: 'card-body', id: 'setup-content' }, [
                        // Step 1: Account Details
                        AF.utils.create('form', { id: 'setup-form-step1', class: 'space-y-5' }, [
                            AF.utils.create('h2', { class: 'text-xl font-semibold mb-2' }, 'Create Owner Account'),
                            AF.utils.create('p', { class: 'text-forge-400 text-sm mb-6' }, 'This will be the single administrator account for your private platform.'),

                            AF.utils.create('div', { class: 'form-group' }, [
                                AF.utils.create('label', { class: 'form-label', for: 'setup-email' }, 'Email Address'),
                                AF.utils.create('input', {
                                    type: 'email',
                                    id: 'setup-email',
                                    name: 'email',
                                    class: 'form-input',
                                    placeholder: 'owner@yourdomain.com',
                                    autocomplete: 'email',
                                    required: true,
                                    autofocus: true,
                                }),
                                AF.utils.create('p', { class: 'form-help' }, 'This email will be used for login and recovery'),
                            ]),

                            AF.utils.create('div', { class: 'form-group' }, [
                                AF.utils.create('label', { class: 'form-label', for: 'setup-name' }, 'Display Name'),
                                AF.utils.create('input', {
                                    type: 'text',
                                    id: 'setup-name',
                                    name: 'display_name',
                                    class: 'form-input',
                                    placeholder: 'Sebinesh',
                                    autocomplete: 'name',
                                    required: true,
                                    maxlength: 100,
                                }),
                            ]),

                            AF.utils.create('div', { class: 'form-group' }, [
                                AF.utils.create('label', { class: 'form-label', for: 'setup-password' }, 'Password'),
                                AF.utils.create('div', { class: 'relative' }, [
                                    AF.utils.create('input', {
                                        type: 'password',
                                        id: 'setup-password',
                                        name: 'password',
                                        class: 'form-input pr-12',
                                        placeholder: '••••••••••••',
                                        autocomplete: 'new-password',
                                        required: true,
                                        minlength: 12,
                                    }),
                                    AF.utils.create('button', {
                                        type: 'button',
                                        id: 'toggle-setup-password',
                                        class: 'absolute right-3 top-1/2 -translate-y-1/2 text-forge-400 hover:text-forge-200',
                                    }, '👁'),
                                ]),
                                AF.utils.create('p', { class: 'form-help' }, 'Minimum 12 characters with upper, lower, number, and special character'),
                            ]),

                            AF.utils.create('div', { class: 'form-group' }, [
                                AF.utils.create('label', { class: 'form-label', for: 'setup-confirm' }, 'Confirm Password'),
                                AF.utils.create('input', {
                                    type: 'password',
                                    id: 'setup-confirm',
                                    name: 'confirm_password',
                                    class: 'form-input',
                                    placeholder: '••••••••••••',
                                    autocomplete: 'new-password',
                                    required: true,
                                }),
                            ]),

                            // Password strength indicator
                            AF.utils.create('div', { class: 'mt-2', id: 'password-strength' }, [
                                AF.utils.create('div', { class: 'flex gap-1 mb-1' }, [
                                    ...Array.from({ length: 4 }, (_, i) => AF.utils.create('div', {
                                        class: 'h-1.5 flex-1 rounded-full bg-forge-800 transition-colors',
                                        id: `strength-bar-${i}`,
                                    })),
                                ]),
                                AF.utils.create('p', { class: 'text-xs text-forge-500', id: 'strength-text' }, 'Password strength: Very weak'),
                            ]),

                            AF.utils.create('div', { class: 'form-group' }, [
                                AF.utils.create('label', { class: 'flex items-start gap-2 cursor-pointer' }, [
                                    AF.utils.create('input', {
                                        type: 'checkbox',
                                        id: 'setup-master-key-custom',
                                        name: 'custom_master_key',
                                        class: 'w-4 h-4 mt-0.5 rounded border-forge-600 bg-forge-800 text-accent-500 focus:ring-accent-500',
                                    }),
                                    AF.utils.create('div', {}, [
                                        AF.utils.create('span', { class: 'text-sm font-medium text-forge-300' }, 'Provide custom Master API Key'),
                                        AF.utils.create('p', { class: 'text-xs text-forge-500 mt-0.5' }, 'Leave unchecked to generate a secure key automatically'),
                                    ]),
                                ]),
                            ]),

                            AF.utils.create('div', { id: 'custom-master-key-field', class: 'hidden form-group' }, [
                                AF.utils.create('label', { class: 'form-label', for: 'setup-master-key' }, 'Master API Key'),
                                AF.utils.create('div', { class: 'relative' }, [
                                    AF.utils.create('input', {
                                        type: 'text',
                                        id: 'setup-master-key',
                                        name: 'master_api_key',
                                        class: 'form-input font-mono',
                                        placeholder: 'af_master_...',
                                        autocomplete: 'off',
                                    }),
                                    AF.utils.create('button', {
                                        type: 'button',
                                        id: 'toggle-master-key',
                                        class: 'absolute right-3 top-1/2 -translate-y-1/2 text-forge-400 hover:text-forge-200',
                                    }, '👁'),
                                ]),
                            ]),

                            AF.utils.create('button', {
                                type: 'submit',
                                class: 'btn btn-primary btn-block btn-lg mt-4',
                                id: 'setup-next-btn',
                            }, 'Continue to Master Key'),
                        ]),

                        // Step 2: Master Key (shown after step 1)
                        AF.utils.create('div', { id: 'setup-step2', class: 'hidden space-y-5' }, [
                            AF.utils.create('div', { class: 'flex items-center gap-3 p-4 bg-accent-500/10 border border-accent-500/20 rounded-lg' }, [
                                AF.utils.create('div', { class: 'w-10 h-10 rounded-lg bg-accent-500/20 flex items-center justify-center flex-shrink-0' }, [
                                    AF.utils.create('svg', { class: 'w-5 h-5 text-accent-500', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                                        AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z' }),
                                    ]),
                                ]),
                                AF.utils.create('div', {}, [
                                    AF.utils.create('h3', { class: 'font-semibold text-accent-400' }, 'Master API Key Generated'),
                                    AF.utils.create('p', { class: 'text-sm text-forge-400' }, 'Save this key securely - it provides full platform access'),
                                ]),
                            ]),

                            AF.utils.create('div', { class: 'p-4 bg-forge-900/50 border border-forge-700 rounded-lg font-mono text-lg break-all select-all', id: 'master-key-display' }),
                            AF.utils.create('p', { class: 'text-xs text-forge-500 text-center' }, 'Tap to select all · Long press to copy'),

                            AF.utils.create('div', { class: 'flex gap-2' }, [
                                AF.utils.create('button', { type: 'button', class: 'btn btn-secondary flex-1', id: 'copy-master-key' }, 'Copy Key'),
                                AF.utils.create('button', { type: 'button', class: 'btn btn-primary flex-1', id: 'setup-complete-btn' }, 'Complete Setup'),
                            ]),

                            AF.utils.create('p', { class: 'text-xs text-forge-500 text-center' }, '⚠️ This key will never be shown again. Store it in a password manager.'),
                        ]),
                    ]),
                ]),

                // Security notice
                AF.utils.create('div', { class: 'mt-6 text-center text-xs text-forge-500' }, [
                    AF.utils.create('p', {}, '🔒 Single-owner platform · No public registration · End-to-end encryption'),
                ]),
            ]),
        ]);
    },

    mount() {
        const form = document.getElementById('setup-form-step1');
        const passwordInput = document.getElementById('setup-password');
        const confirmInput = document.getElementById('setup-confirm');
        const customKeyCheckbox = document.getElementById('setup-master-key-custom');
        const customKeyField = document.getElementById('custom-master-key-field');
        const masterKeyInput = document.getElementById('setup-master-key');
        const togglePassword = document.getElementById('toggle-setup-password');
        const toggleMasterKey = document.getElementById('toggle-master-key');
        const nextBtn = document.getElementById('setup-next-btn');
        const step1 = document.getElementById('setup-form-step1');
        const step2 = document.getElementById('setup-step2');
        const masterKeyDisplay = document.getElementById('master-key-display');
        const copyKeyBtn = document.getElementById('copy-master-key');
        const completeBtn = document.getElementById('setup-complete-btn');
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');

        let generatedMasterKey = null;

        // Toggle password visibility
        togglePassword.addEventListener('click', () => {
            const type = passwordInput.type === 'password' ? 'text' : 'password';
            passwordInput.type = type;
            togglePassword.textContent = type === 'password' ? '👁' : '🙈';
        });

        toggleMasterKey.addEventListener('click', () => {
            const type = masterKeyInput.type === 'text' ? 'password' : 'text';
            masterKeyInput.type = type;
            toggleMasterKey.textContent = type === 'text' ? '👁' : '🙈';
        });

        // Custom master key checkbox
        customKeyCheckbox.addEventListener('change', () => {
            customKeyField.classList.toggle('hidden', !customKeyCheckbox.checked);
            if (!customKeyCheckbox.checked) {
                masterKeyInput.value = '';
            }
        });

        // Password strength meter
        passwordInput.addEventListener('input', () => {
            updatePasswordStrength(passwordInput.value);
            validateForm();
        });

        confirmInput.addEventListener('input', validateForm);

        function updatePasswordStrength(password) {
            let strength = 0;
            const checks = [
                password.length >= 12,
                /[A-Z]/.test(password),
                /[a-z]/.test(password),
                /[0-9]/.test(password),
                /[^A-Za-z0-9]/.test(password),
            ];

            checks.forEach((check, i) => {
                if (check) strength++;
                const bar = document.getElementById(`strength-bar-${i}`);
                if (bar) {
                    bar.style.backgroundColor = check ? getStrengthColor(strength) : '#334155';
                }
            });

            const labels = ['Very weak', 'Weak', 'Fair', 'Good', 'Strong'];
            const textEl = document.getElementById('strength-text');
            if (textEl) textEl.textContent = `Password strength: ${labels[Math.min(strength, 4)]}`;
        }

        function getStrengthColor(strength) {
            if (strength <= 1) return '#ef4444';
            if (strength <= 2) return '#f59e0b';
            if (strength <= 3) return '#3b82f6';
            return '#22c55e';
        }

        function validateForm() {
            const email = document.getElementById('setup-email').value;
            const name = document.getElementById('setup-name').value;
            const password = passwordInput.value;
            const confirm = confirmInput.value;
            const customKey = customKeyCheckbox.checked ? masterKeyInput.value.trim() : null;

            const valid = email && name && password.length >= 12 && password === confirm &&
                (!customKeyCheckbox.checked || (customKey && customKey.startsWith('af_master_')));

            nextBtn.disabled = !valid;
        }

        // Form submission (Step 1)
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (nextBtn.disabled) return;

            const data = {
                email: document.getElementById('setup-email').value.trim(),
                display_name: document.getElementById('setup-name').value.trim(),
                password: passwordInput.value,
            };

            if (customKeyCheckbox.checked) {
                data.master_api_key = masterKeyInput.value.trim();
            }

            nextBtn.disabled = true;
            nextBtn.innerHTML = '<span class="spinner spinner-sm"></span> Creating account...';

            try {
                const result = await AF.utils.post('/auth/setup', data);
                generatedMasterKey = result.master_api_key;

                // Show step 2
                step1.classList.add('hidden');
                step2.classList.remove('hidden');
                masterKeyDisplay.textContent = generatedMasterKey;

                progressBar.style.width = '100%';
                progressText.textContent = 'Master Key Generated';

                AF.toast.success('Account created successfully!');
            } catch (error) {
                AF.toast.error(error.message || 'Setup failed');
                nextBtn.disabled = false;
                nextBtn.textContent = 'Continue to Master Key';
            }
        });

        // Copy master key
        copyKeyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(generatedMasterKey);
                copyKeyBtn.textContent = 'Copied!';
                setTimeout(() => copyKeyBtn.textContent = 'Copy Key', 2000);
                AF.toast.success('Master key copied to clipboard');
            } catch {
                AF.toast.error('Failed to copy');
            }
        });

        // Complete setup
        completeBtn.addEventListener('click', () => {
            AF.router.navigate(AF.CONFIG.ROUTES.LOGIN);
        });

        // Initial validation
        validateForm();
    },
};