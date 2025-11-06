/**
 * API Module
 * Handles REST API calls to backend
 */

const API = {
    BASE_URL: 'http://localhost:8080/api',

    /**
     * Get all transcriptions with optional filters
     */
    async getTranscriptions(params = {}) {
        try {
            const queryParams = new URLSearchParams();

            if (params.status) queryParams.append('status', params.status);
            if (params.language) queryParams.append('language', params.language);
            if (params.search) queryParams.append('search', params.search);
            if (params.page) queryParams.append('page', params.page);

            const url = `${this.BASE_URL}/transcriptions/?${queryParams.toString()}`;
            const response = await Auth.fetch(url);

            if (!response.ok) {
                throw new Error('Failed to fetch transcriptions');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * Get transcription details by ID
     */
    async getTranscription(id) {
        try {
            const response = await Auth.fetch(`${this.BASE_URL}/transcriptions/${id}/`);

            if (!response.ok) {
                throw new Error('Failed to fetch transcription');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * Delete transcription
     */
    async deleteTranscription(id) {
        try {
            const response = await Auth.fetch(`${this.BASE_URL}/transcriptions/${id}/`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete transcription');
            }

            return true;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * Get user statistics
     */
    async getStatistics() {
        try {
            const response = await Auth.fetch(`${this.BASE_URL}/transcriptions/stats/`);

            if (!response.ok) {
                throw new Error('Failed to fetch statistics');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * Get supported languages
     */
    async getLanguages() {
        try {
            const response = await Auth.fetch(`${this.BASE_URL}/transcriptions/languages/`);

            if (!response.ok) {
                throw new Error('Failed to fetch languages');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * Export transcription as text file
     */
    async exportTranscription(id) {
        try {
            const response = await Auth.fetch(`${this.BASE_URL}/transcriptions/${id}/export/`);

            if (!response.ok) {
                throw new Error('Failed to export transcription');
            }

            const text = await response.text();
            const blob = new Blob([text], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `transcription_${id}.txt`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            return true;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
};
