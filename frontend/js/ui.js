/**
 * UI Module
 * Handles DOM manipulation and UI updates
 */

const UI = {
    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastIcon = document.getElementById('toastIcon');
        const toastMessage = document.getElementById('toastMessage');

        if (!toast || !toastIcon || !toastMessage) {
            console.log('Toast notification:', message);
            return;
        }

        // Set icon based on type
        const icons = {
            'success': 'check_circle',
            'error': 'error',
            'warning': 'warning',
            'info': 'info'
        };

        toastIcon.textContent = icons[type] || icons['info'];
        toastMessage.textContent = message;

        // Set color class and show
        toast.className = 'toast ' + type;
        toast.classList.remove('hidden');

        // Hide after 4 seconds
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 4000);
    },

    /**
     * Update connection status
     */
    updateConnectionStatus(status) {
        const statusIndicator = document.getElementById('connectionStatus');
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('.status-text');

        if (status === 'connected') {
            statusDot.className = 'status-dot status-connected';
            statusText.textContent = 'Connected';
        } else {
            statusDot.className = 'status-dot status-disconnected';
            statusText.textContent = 'Disconnected';
        }
    },

    /**
     * Update live transcription display
     */
    updateLiveTranscription(text) {
        const liveTranscription = document.getElementById('liveTranscription');
        liveTranscription.innerHTML = `<p class="transcription-text">${this.escapeHtml(text)}</p>`;
    },

    /**
     * Clear live transcription
     */
    clearLiveTranscription() {
        const liveTranscription = document.getElementById('liveTranscription');
        liveTranscription.innerHTML = '<p class="placeholder">Start recording to see transcription here...</p>';
    },

    /**
     * Update statistics
     */
    updateStatistics(stats) {
        document.getElementById('totalCount').textContent = stats.total_transcriptions || 0;
        document.getElementById('completedCount').textContent = stats.completed || 0;
        document.getElementById('failedCount').textContent = stats.failed || 0;

        // Convert total duration from seconds to minutes
        const minutes = Math.round((stats.total_duration || 0) / 60);
        document.getElementById('totalDuration').textContent = minutes;
    },

    /**
     * Render history list
     */
    renderHistory(data) {
        const historyList = document.getElementById('historyList');

        if (!data.results || data.results.length === 0) {
            historyList.innerHTML = `
                <div class="empty-state">
                    <span class="material-icons">inbox</span>
                    <p>No transcriptions found</p>
                </div>
            `;
            return;
        }

        historyList.innerHTML = data.results.map(item => this.createHistoryItem(item)).join('');

        // Update pagination
        this.updatePagination(data);
    },

    /**
     * Create history item HTML
     */
    createHistoryItem(item) {
        const statusClass = `status-${item.status}`;
        const date = new Date(item.created_at).toLocaleString();

        return `
            <div class="history-item" data-id="${item.id}">
                <div class="history-item-content">
                    <div class="history-item-header">
                        <span class="material-icons">description</span>
                        <span class="status-badge ${statusClass}">${item.status}</span>
                    </div>
                    <div class="history-item-text">${this.escapeHtml(item.preview_text || 'No text available')}</div>
                    <div class="history-item-meta">
                        <span class="meta-item">
                            <span class="material-icons">language</span>
                            ${item.language_name}
                        </span>
                        <span class="meta-item">
                            <span class="material-icons">schedule</span>
                            ${date}
                        </span>
                        ${item.audio_duration ? `
                            <span class="meta-item">
                                <span class="material-icons">timer</span>
                                ${Math.round(item.audio_duration)}s
                            </span>
                        ` : ''}
                    </div>
                </div>
                <div class="history-item-actions">
                    <button class="action-btn" onclick="viewTranscription(${item.id})" title="View details">
                        <span class="material-icons">visibility</span>
                    </button>
                    <button class="action-btn" onclick="exportTranscription(${item.id})" title="Export">
                        <span class="material-icons">download</span>
                    </button>
                    <button class="action-btn" onclick="deleteTranscription(${item.id})" title="Delete">
                        <span class="material-icons">delete</span>
                    </button>
                </div>
            </div>
        `;
    },

    /**
     * Update pagination
     */
    updatePagination(data) {
        const pagination = document.getElementById('pagination');
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        const pageInfo = document.getElementById('pageInfo');

        if (data.count <= 10) {
            pagination.classList.add('hidden');
            return;
        }

        pagination.classList.remove('hidden');

        // Calculate current page
        const currentPage = data.previous ? parseInt(new URLSearchParams(data.previous).get('page') || '0') + 1 : 1;
        const totalPages = Math.ceil(data.count / 10);

        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;

        prevBtn.disabled = !data.previous;
        nextBtn.disabled = !data.next;

        prevBtn.onclick = data.previous ? () => window.loadHistory(currentPage - 1) : null;
        nextBtn.onclick = data.next ? () => window.loadHistory(currentPage + 1) : null;
    },

    /**
     * Show transcription details modal
     */
    showTranscriptionDetail(transcription) {
        const modal = document.getElementById('detailModal');
        const content = document.getElementById('detailContent');

        const date = new Date(transcription.created_at).toLocaleString();
        const completedDate = transcription.completed_at ?
            new Date(transcription.completed_at).toLocaleString() : 'N/A';

        content.innerHTML = `
            <div class="detail-section">
                <h3>Transcription Text</h3>
                <div class="transcription-box">
                    <p class="transcription-text">${this.escapeHtml(transcription.transcription_text || 'No text available')}</p>
                </div>
            </div>

            <div class="detail-section">
                <h3>Details</h3>
                <table class="detail-table">
                    <tr>
                        <th>Language:</th>
                        <td>${transcription.language_name}</td>
                    </tr>
                    <tr>
                        <th>Status:</th>
                        <td><span class="status-badge status-${transcription.status}">${transcription.status_display}</span></td>
                    </tr>
                    <tr>
                        <th>Created:</th>
                        <td>${date}</td>
                    </tr>
                    <tr>
                        <th>Completed:</th>
                        <td>${completedDate}</td>
                    </tr>
                    ${transcription.audio_duration ? `
                    <tr>
                        <th>Duration:</th>
                        <td>${Math.round(transcription.audio_duration)} seconds</td>
                    </tr>
                    ` : ''}
                    ${transcription.processing_time ? `
                    <tr>
                        <th>Processing Time:</th>
                        <td>${transcription.processing_time.toFixed(2)} seconds</td>
                    </tr>
                    ` : ''}
                    ${transcription.confidence_score ? `
                    <tr>
                        <th>Confidence:</th>
                        <td>${(transcription.confidence_score * 100).toFixed(1)}%</td>
                    </tr>
                    ` : ''}
                    ${transcription.error_message ? `
                    <tr>
                        <th>Error:</th>
                        <td class="error-message">${this.escapeHtml(transcription.error_message)}</td>
                    </tr>
                    ` : ''}
                </table>
            </div>
        `;

        modal.classList.remove('hidden');
    },

    /**
     * Close detail modal
     */
    closeDetailModal() {
        const modal = document.getElementById('detailModal');
        modal.classList.add('hidden');
    },

    /**
     * Show loading state
     */
    showLoading(elementId) {
        const element = document.getElementById(elementId);
        element.innerHTML = '<div class="loading">Loading...</div>';
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Global functions for onclick handlers
function viewTranscription(id) {
    window.viewTranscription(id);
}

function exportTranscription(id) {
    window.exportTranscription(id);
}

function deleteTranscription(id) {
    window.deleteTranscription(id);
}

function closeDetailModal() {
    UI.closeDetailModal();
}
