/**
 * Main Application Module
 * Orchestrates all other modules and handles user interactions
 */

const App = {
    currentLanguage: 'hi-IN',
    isRecording: false,
    currentFilters: {
        status: '',
        language: '',
        search: ''
    },
    currentPage: 1,

    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing application...');

        // Check browser compatibility
        if (!AudioRecorder.isSupported()) {
            alert('Your browser does not support audio recording. Please use Chrome, Firefox, or Edge.');
            return;
        }

        // Setup event listeners first
        this.setupEventListeners();

        // Setup WebSocket callbacks
        this.setupWebSocketCallbacks();

        // Check authentication
        if (Auth.isAuthenticated()) {
            this.showMainApp();
            await this.loadInitialData();
        } else {
            this.showLogin();
        }

        console.log('Application initialized');
    },

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Use event delegation and wait for DOM
        setTimeout(() => {
            // Login form
            const loginForm = document.getElementById('loginForm');
            if (loginForm) {
                loginForm.addEventListener('submit', (e) => this.handleLogin(e));
            }

            // Logout button
            const logoutBtn = document.getElementById('logoutBtn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', () => this.handleLogout());
            }

            // Language selector
            const languageSelect = document.getElementById('languageSelect');
            if (languageSelect) {
                languageSelect.addEventListener('change', (e) => {
                    this.currentLanguage = e.target.value;
                });
            }

            // Recording controls
            const startBtn = document.getElementById('startRecordBtn');
            const stopBtn = document.getElementById('stopRecordBtn');

            if (startBtn) {
                startBtn.addEventListener('click', () => this.startRecording());
            }

            if (stopBtn) {
                stopBtn.addEventListener('click', () => this.stopRecording());
            }

            // File upload controls
            const dropZone = document.getElementById('dropZone');
            const audioFileInput = document.getElementById('audioFileInput');
            const browseFileBtn = document.getElementById('browseFileBtn');

            if (dropZone && audioFileInput) {
                // Drag and drop
                dropZone.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    dropZone.classList.add('drag-over');
                });

                dropZone.addEventListener('dragleave', () => {
                    dropZone.classList.remove('drag-over');
                });

                dropZone.addEventListener('drop', (e) => {
                    e.preventDefault();
                    dropZone.classList.remove('drag-over');
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        this.handleFileUpload(files[0]);
                    }
                });

                // Click to browse
                dropZone.addEventListener('click', (e) => {
                    if (e.target.id !== 'browseFileBtn') {
                        audioFileInput.click();
                    }
                });

                if (browseFileBtn) {
                    browseFileBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        audioFileInput.click();
                    });
                }

                audioFileInput.addEventListener('change', (e) => {
                    const files = e.target.files;
                    if (files.length > 0) {
                        this.handleFileUpload(files[0]);
                    }
                });
            }

            // Search and filters
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    this.currentFilters.search = e.target.value;
                    this.debouncedLoadHistory();
                });
            }

            const statusFilter = document.getElementById('statusFilter');
            if (statusFilter) {
                statusFilter.addEventListener('change', (e) => {
                    this.currentFilters.status = e.target.value;
                    this.loadHistory();
                });
            }

            const languageFilter = document.getElementById('languageFilter');
            if (languageFilter) {
                languageFilter.addEventListener('change', (e) => {
                    this.currentFilters.language = e.target.value;
                    this.loadHistory();
                });
            }

            // Refresh button
            const refreshBtn = document.getElementById('refreshBtn');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => this.loadHistory());
            }
        }, 100);
    },

    /**
     * Setup WebSocket callbacks
     */
    setupWebSocketCallbacks() {
        // Status change callback
        WebSocketClient.setOnStatusChange((status) => {
            UI.updateConnectionStatus(status);
        });

        // Transcription update callback
        WebSocketClient.setOnTranscription((text, fullText) => {
            UI.updateLiveTranscription(fullText);
        });

        // Final transcription callback
        WebSocketClient.setOnFinal((text, transcriptionId) => {
            UI.showToast('Transcription completed!', 'success');
            UI.updateLiveTranscription(text);

            // Reload history and stats
            setTimeout(() => {
                this.loadHistory();
                this.loadStatistics();
            }, 1000);
        });

        // Error callback
        WebSocketClient.setOnError((error) => {
            UI.showToast(error, 'error');
        });
    },

    /**
     * Handle login form submission
     */
    async handleLogin(event) {
        event.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const loginError = document.getElementById('loginError');
        const loginBtn = document.querySelector('#loginForm button[type="submit"]');

        // Clear previous error
        loginError.classList.add('hidden');
        loginBtn.disabled = true;
        loginBtn.textContent = 'Logging in...';

        try {
            const result = await Auth.login(username, password);

            if (result.success) {
                UI.showToast('Login successful!', 'success');
                this.showMainApp();
                await this.loadInitialData();
            } else {
                loginError.textContent = result.error || 'Login failed';
                loginError.classList.remove('hidden');
            }
        } catch (error) {
            loginError.textContent = error.message || 'Login failed';
            loginError.classList.remove('hidden');
        } finally {
            loginBtn.disabled = false;
            loginBtn.textContent = 'Login';
        }
    },

    /**
     * Handle logout
     */
    handleLogout() {
        // Stop recording if active
        if (this.isRecording) {
            this.stopRecording();
        }

        // Disconnect WebSocket
        WebSocketClient.disconnect();

        // Clear auth
        Auth.logout();

        // Show login
        this.showLogin();

        UI.showToast('Logged out successfully', 'info');
    },

    /**
     * Show login modal
     */
    showLogin() {
        const loginModal = document.getElementById('loginModal');
        const mainApp = document.getElementById('mainApp');

        if (loginModal) {
            loginModal.classList.remove('hidden');
        }

        if (mainApp) {
            mainApp.classList.add('hidden');
        }

        // Clear form
        const loginForm = document.getElementById('loginForm');
        const loginError = document.getElementById('loginError');

        if (loginForm) {
            loginForm.reset();
        }

        if (loginError) {
            loginError.classList.add('hidden');
        }
    },

    /**
     * Show main application
     */
    showMainApp() {
        const loginModal = document.getElementById('loginModal');
        const mainApp = document.getElementById('mainApp');

        if (loginModal) {
            loginModal.classList.add('hidden');
        }

        if (mainApp) {
            mainApp.classList.remove('hidden');
        }

        // Update user display
        const userInfo = Auth.getUserInfo();
        const userEmail = document.getElementById('userEmail');
        if (userEmail && userInfo) {
            userEmail.textContent = userInfo.email;
        }
    },

    /**
     * Load initial data
     */
    async loadInitialData() {
        await Promise.all([
            this.loadStatistics(),
            this.loadHistory()
        ]);
    },

    /**
     * Load user statistics
     */
    async loadStatistics() {
        try {
            const stats = await API.getStatistics();
            UI.updateStatistics(stats);
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    },

    /**
     * Load transcription history
     */
    async loadHistory(page = 1) {
        try {
            UI.showLoading('historyList');

            const params = {
                page,
                ...this.currentFilters
            };

            // Remove empty filters
            Object.keys(params).forEach(key => {
                if (!params[key]) delete params[key];
            });

            const data = await API.getTranscriptions(params);
            UI.renderHistory(data);

            this.currentPage = page;
        } catch (error) {
            console.error('Failed to load history:', error);
            UI.showToast('Failed to load history', 'error');
        }
    },

    /**
     * Debounced load history (for search input)
     */
    debouncedLoadHistory: (() => {
        let timeout;
        return function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                this.loadHistory();
            }, 500);
        };
    })(),

    /**
     * Start recording
     */
    async startRecording() {
        if (this.isRecording) {
            UI.showToast('Already recording', 'warning');
            return;
        }

        try {
            const startBtn = document.getElementById('startRecordBtn');
            const stopBtn = document.getElementById('stopRecordBtn');

            // Update UI
            startBtn.disabled = true;
            stopBtn.disabled = false;
            stopBtn.classList.remove('hidden');
            UI.clearLiveTranscription();

            // Connect WebSocket
            UI.showToast('Connecting...', 'info');
            await WebSocketClient.connect(this.currentLanguage);

            // Start audio recording
            UI.showToast('Starting recording...', 'info');
            await AudioRecorder.startRecording((audioData) => {
                // Send audio chunks to WebSocket
                WebSocketClient.sendAudio(audioData);
            });

            this.isRecording = true;
            UI.showToast('Recording started. Speak now!', 'success');

        } catch (error) {
            console.error('Failed to start recording:', error);
            UI.showToast(error.message || 'Failed to start recording', 'error');

            // Reset UI
            const startBtn = document.getElementById('startRecordBtn');
            const stopBtn = document.getElementById('stopRecordBtn');
            startBtn.disabled = false;
            stopBtn.disabled = true;
            stopBtn.classList.add('hidden');

            // Cleanup
            WebSocketClient.disconnect();
        }
    },

    /**
     * Stop recording
     */
    stopRecording() {
        if (!this.isRecording) {
            return;
        }

        const startBtn = document.getElementById('startRecordBtn');
        const stopBtn = document.getElementById('stopRecordBtn');

        // Update UI
        startBtn.disabled = false;
        stopBtn.disabled = true;
        stopBtn.classList.add('hidden');

        // Stop audio recording
        AudioRecorder.stopRecording();

        // Send end signal
        WebSocketClient.sendEnd();

        // Disconnect WebSocket after a delay (to receive final transcription)
        setTimeout(() => {
            WebSocketClient.disconnect();
        }, 2000);

        this.isRecording = false;
        UI.showToast('Recording stopped. Processing...', 'info');
    },

    /**
     * Handle file upload
     */
    async handleFileUpload(file) {
        // Validate file type
        if (!file.type.startsWith('audio/')) {
            UI.showToast('Please select an audio file', 'error');
            return;
        }

        // Validate file size (25MB)
        const maxSize = 25 * 1024 * 1024;
        if (file.size > maxSize) {
            UI.showToast('File size exceeds 25MB limit', 'error');
            return;
        }

        // Get language
        const languageSelect = document.getElementById('uploadLanguageSelect');
        const languageCode = languageSelect ? languageSelect.value : 'hi-IN';

        // Show progress
        const uploadProgress = document.getElementById('uploadProgress');
        const uploadResult = document.getElementById('uploadResult');
        const progressFill = document.getElementById('progressFill');
        const uploadStatus = document.getElementById('uploadStatus');

        uploadProgress.classList.remove('hidden');
        uploadResult.classList.add('hidden');

        try {
            // Create FormData
            const formData = new FormData();
            formData.append('audio_file', file);
            formData.append('language_code', languageCode);

            // Upload with progress
            uploadStatus.textContent = 'Uploading...';
            progressFill.style.width = '30%';

            const token = Auth.getToken();
            const response = await fetch(`${API.API_URL}/transcriptions/upload/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Upload failed');
            }

            uploadStatus.textContent = 'Processing...';
            progressFill.style.width = '60%';

            const result = await response.json();

            // Complete progress
            progressFill.style.width = '100%';
            uploadStatus.textContent = 'Complete!';

            // Hide progress after delay
            setTimeout(() => {
                uploadProgress.classList.add('hidden');
            }, 1000);

            // Show result
            const uploadTranscriptionText = document.getElementById('uploadTranscriptionText');
            if (uploadTranscriptionText) {
                uploadTranscriptionText.textContent = result.transcription_text || 'No transcription available';
            }
            uploadResult.classList.remove('hidden');

            UI.showToast('Transcription completed successfully!', 'success');

            // Reload history and stats
            setTimeout(() => {
                this.loadHistory();
                this.loadStatistics();
            }, 1000);

            // Reset file input
            const audioFileInput = document.getElementById('audioFileInput');
            if (audioFileInput) {
                audioFileInput.value = '';
            }

        } catch (error) {
            console.error('Upload failed:', error);
            uploadProgress.classList.add('hidden');
            UI.showToast(error.message || 'Upload failed', 'error');

            // Reset file input
            const audioFileInput = document.getElementById('audioFileInput');
            if (audioFileInput) {
                audioFileInput.value = '';
            }
        }
    }
};

// Global functions for onclick handlers (called from UI module)
window.viewTranscription = async function(id) {
    try {
        const transcription = await API.getTranscription(id);
        UI.showTranscriptionDetail(transcription);
    } catch (error) {
        UI.showToast('Failed to load transcription details', 'error');
    }
};

window.exportTranscription = async function(id) {
    try {
        await API.exportTranscription(id);
        UI.showToast('Transcription exported successfully', 'success');
    } catch (error) {
        UI.showToast('Failed to export transcription', 'error');
    }
};

window.deleteTranscription = async function(id) {
    if (!confirm('Are you sure you want to delete this transcription?')) {
        return;
    }

    try {
        await API.deleteTranscription(id);
        UI.showToast('Transcription deleted successfully', 'success');

        // Reload data
        App.loadHistory(App.currentPage);
        App.loadStatistics();
    } catch (error) {
        UI.showToast('Failed to delete transcription', 'error');
    }
};

window.loadHistory = function(page) {
    App.loadHistory(page);
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});

// Handle page visibility changes (pause/resume recording)
document.addEventListener('visibilitychange', () => {
    if (document.hidden && App.isRecording) {
        console.log('Page hidden, stopping recording');
        App.stopRecording();
    }
});
