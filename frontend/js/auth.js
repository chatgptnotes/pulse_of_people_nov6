/**
 * Authentication Module
 * Handles login, logout, token management
 */

const Auth = {
    // Configuration - Auto-detect environment
    API_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8080/api'
        : 'https://pulseofpeoplenov6-production.up.railway.app/api',

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        const token = this.getToken();
        if (!token) return false;

        // Check if token is expired
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const now = Date.now() / 1000;
            return payload.exp > now;
        } catch (e) {
            return false;
        }
    },

    /**
     * Get stored access token
     */
    getToken() {
        return localStorage.getItem('access_token');
    },

    /**
     * Get stored refresh token
     */
    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    },

    /**
     * Store tokens
     */
    setTokens(accessToken, refreshToken) {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    },

    /**
     * Get user info from token
     */
    getUserInfo() {
        const token = this.getToken();
        if (!token) return null;

        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return {
                id: payload.user_id,
                email: payload.email || payload.username,
                exp: payload.exp
            };
        } catch (e) {
            return null;
        }
    },

    /**
     * Login with credentials
     */
    async login(username, password) {
        try {
            const response = await fetch(`${this.API_URL}/auth/login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();
            this.setTokens(data.access, data.refresh);

            return {
                success: true,
                user: data.user || this.getUserInfo()
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    },

    /**
     * Refresh access token
     */
    async refreshToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }

        try {
            const response = await fetch(`${this.API_URL}/auth/refresh/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh: refreshToken })
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            this.setTokens(data.access, refreshToken);

            return data.access;
        } catch (error) {
            this.logout();
            throw error;
        }
    },

    /**
     * Logout user
     */
    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_email');
    },

    /**
     * Make authenticated API request
     */
    async fetch(url, options = {}) {
        const token = this.getToken();

        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            let response = await fetch(url, {
                ...options,
                headers
            });

            // If unauthorized, try to refresh token
            if (response.status === 401) {
                await this.refreshToken();
                const newToken = this.getToken();
                headers['Authorization'] = `Bearer ${newToken}`;

                // Retry request with new token
                response = await fetch(url, {
                    ...options,
                    headers
                });
            }

            return response;
        } catch (error) {
            throw error;
        }
    }
};
