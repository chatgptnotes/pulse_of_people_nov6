// JioTV Player JavaScript
const API_BASE_URL = 'http://localhost:8080/api/jiotv';

// Global state
let currentQuality = 'auto';
let currentChannel = null;
let hlsInstance = null;
let currentSession = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    attachEventListeners();
});

// Initialize application
async function initializeApp() {
    await checkServiceHealth();
    await loadTamilNewsChannels();
    await loadStatistics();
    checkAuthStatus();
}

// Attach event listeners
function attachEventListeners() {
    // Login button
    document.getElementById('loginBtn').addEventListener('click', openAuthModal);

    // Auth status button
    document.getElementById('authStatusBtn').addEventListener('click', showAuthStatus);

    // Send OTP
    document.getElementById('sendOtpBtn').addEventListener('click', sendOTP);

    // OTP Form
    document.getElementById('otpForm').addEventListener('submit', verifyOTP);

    // Password Form
    document.getElementById('passwordForm').addEventListener('submit', loginWithPassword);

    // Refresh channels
    document.getElementById('refreshChannelsBtn').addEventListener('click', refreshChannels);

    // Quality buttons
    document.querySelectorAll('.quality-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const quality = e.target.dataset.quality;
            setQuality(quality);
        });
    });

    // Set auto quality as active by default
    document.querySelector('[data-quality="auto"]').classList.add('active');
}

// Check service health
async function checkServiceHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health/`);
        const data = await response.json();

        const statusCard = document.getElementById('serviceStatus');
        const statusText = document.getElementById('statusText');

        if (data.status === 'online') {
            statusCard.classList.add('online');
            statusText.textContent = 'JioTV Service: Online';
            showToast('Service is online', 'success');
        } else {
            statusCard.classList.add('offline');
            statusText.textContent = 'JioTV Service: Offline';
            showToast('Service is offline', 'error');
        }
    } catch (error) {
        console.error('Health check failed:', error);
        document.getElementById('statusText').textContent = 'JioTV Service: Error';
        showToast('Cannot connect to service', 'error');
    }
}

// Load Tamil news channels
async function loadTamilNewsChannels() {
    const channelsList = document.getElementById('channelsList');
    channelsList.innerHTML = '<div class="loading">Loading channels...</div>';

    try {
        const response = await fetch(`${API_BASE_URL}/channels/tamil-news/`);
        const data = await response.json();

        if (data.channels && data.channels.length > 0) {
            channelsList.innerHTML = '';
            data.channels.forEach(channel => {
                const channelCard = createChannelCard(channel);
                channelsList.appendChild(channelCard);
            });
            showToast(`Loaded ${data.channels.length} channels`, 'success');
        } else {
            channelsList.innerHTML = '<div class="loading">No channels found</div>';
        }
    } catch (error) {
        console.error('Failed to load channels:', error);
        channelsList.innerHTML = '<div class="loading">Error loading channels</div>';
        showToast('Failed to load channels', 'error');
    }
}

// Create channel card
function createChannelCard(channel) {
    const card = document.createElement('div');
    card.className = 'channel-card';
    card.onclick = () => playChannel(channel);

    const img = document.createElement('img');
    img.src = channel.logoUrl || 'https://via.placeholder.com/60?text=TV';
    img.alt = channel.name;
    img.onerror = () => { img.src = 'https://via.placeholder.com/60?text=TV'; };

    const details = document.createElement('div');
    details.className = 'channel-details';

    const name = document.createElement('h3');
    name.textContent = channel.name;

    const info = document.createElement('p');
    info.textContent = `${channel.language || 'Tamil'} | ${channel.category || 'News'}`;

    details.appendChild(name);
    details.appendChild(info);

    const icon = document.createElement('span');
    icon.className = 'material-icons';
    icon.textContent = 'play_circle';

    card.appendChild(img);
    card.appendChild(details);
    card.appendChild(icon);

    return card;
}

// Play channel
async function playChannel(channel) {
    currentChannel = channel;
    const channelId = channel.id;

    // Show loading
    document.getElementById('loadingSpinner').classList.remove('hidden');

    // Get auth token from localStorage (if using JWT)
    const token = localStorage.getItem('access_token');

    try {
        const response = await fetch(`${API_BASE_URL}/stream/${channelId}/?quality=${currentQuality}`, {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });

        if (response.status === 401) {
            showToast('Please login to watch channels', 'error');
            openAuthModal();
            return;
        }

        const data = await response.json();
        const streamUrl = data.stream_url;

        // Update channel info
        document.getElementById('currentChannelName').textContent = channel.name;
        document.getElementById('currentChannelLang').textContent = `${channel.language || 'Tamil'} News`;
        document.getElementById('channelInfo').classList.remove('hidden');

        // Initialize HLS player
        initializePlayer(streamUrl);

        showToast(`Now playing: ${channel.name}`, 'success');
    } catch (error) {
        console.error('Failed to play channel:', error);
        showToast('Failed to play channel', 'error');
    } finally {
        document.getElementById('loadingSpinner').classList.add('hidden');
    }
}

// Initialize HLS player
function initializePlayer(streamUrl) {
    const video = document.getElementById('videoPlayer');

    // Destroy existing instance
    if (hlsInstance) {
        hlsInstance.destroy();
    }

    if (Hls.isSupported()) {
        hlsInstance = new Hls({
            enableWorker: true,
            lowLatencyMode: false,
            backBufferLength: 90
        });

        hlsInstance.loadSource(streamUrl);
        hlsInstance.attachMedia(video);

        hlsInstance.on(Hls.Events.MANIFEST_PARSED, function () {
            video.play();
        });

        hlsInstance.on(Hls.Events.ERROR, function (event, data) {
            console.error('HLS Error:', data);
            if (data.fatal) {
                switch (data.type) {
                    case Hls.ErrorTypes.NETWORK_ERROR:
                        showToast('Network error, trying to recover...', 'error');
                        hlsInstance.startLoad();
                        break;
                    case Hls.ErrorTypes.MEDIA_ERROR:
                        showToast('Media error, trying to recover...', 'error');
                        hlsInstance.recoverMediaError();
                        break;
                    default:
                        showToast('Fatal error, cannot play stream', 'error');
                        hlsInstance.destroy();
                        break;
                }
            }
        });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        // Native HLS support (Safari)
        video.src = streamUrl;
        video.addEventListener('loadedmetadata', function () {
            video.play();
        });
    } else {
        showToast('HLS not supported in this browser', 'error');
    }
}

// Set quality
function setQuality(quality) {
    currentQuality = quality;

    // Update active button
    document.querySelectorAll('.quality-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-quality="${quality}"]`).classList.add('active');

    // Replay current channel with new quality
    if (currentChannel) {
        playChannel(currentChannel);
    }

    showToast(`Quality set to ${quality}`, 'info');
}

// Authentication functions
function openAuthModal() {
    document.getElementById('authModal').classList.add('active');
}

function closeAuthModal() {
    document.getElementById('authModal').classList.remove('active');
}

async function sendOTP() {
    const mobile = document.getElementById('mobileNumber').value;
    const sendBtn = document.getElementById('sendOtpBtn');

    if (!mobile) {
        showMessage('Please enter mobile number', 'error');
        return;
    }

    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';

    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE_URL}/auth/send-otp/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            },
            body: JSON.stringify({ mobile })
        });

        const data = await response.json();

        if (data.success) {
            showMessage('OTP sent successfully! Check your SMS.', 'success');
            document.getElementById('otpInputSection').classList.remove('hidden');
        } else {
            showMessage(data.message || 'Failed to send OTP', 'error');
        }
    } catch (error) {
        console.error('Send OTP error:', error);
        showMessage('Error sending OTP', 'error');
    } finally {
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<span class="material-icons">send</span> Send OTP';
    }
}

async function verifyOTP(e) {
    e.preventDefault();

    const mobile = document.getElementById('mobileNumber').value;
    const otp = document.getElementById('otpCode').value;

    if (!mobile || !otp) {
        showMessage('Please enter mobile number and OTP', 'error');
        return;
    }

    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE_URL}/auth/verify-otp/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            },
            body: JSON.stringify({ mobile, otp })
        });

        const data = await response.json();

        if (data.success) {
            showMessage('Authentication successful!', 'success');
            closeAuthModal();
            showToast('Logged in successfully', 'success');
            checkAuthStatus();
        } else {
            showMessage(data.message || 'Authentication failed', 'error');
        }
    } catch (error) {
        console.error('Verify OTP error:', error);
        showMessage('Error verifying OTP', 'error');
    }
}

async function loginWithPassword(e) {
    e.preventDefault();

    const mobile = document.getElementById('mobilePwd').value;
    const password = document.getElementById('password').value;

    if (!mobile || !password) {
        showMessage('Please enter mobile number and password', 'error');
        return;
    }

    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE_URL}/auth/password/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            },
            body: JSON.stringify({ mobile, password })
        });

        const data = await response.json();

        if (data.success) {
            showMessage('Authentication successful!', 'success');
            closeAuthModal();
            showToast('Logged in successfully', 'success');
            checkAuthStatus();
        } else {
            showMessage(data.message || 'Authentication failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('Error during login', 'error');
    }
}

async function checkAuthStatus() {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        const response = await fetch(`${API_BASE_URL}/auth/status/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const data = await response.json();

        if (data.authenticated) {
            document.getElementById('loginBtn').style.display = 'none';
            document.getElementById('userInfo').classList.remove('hidden');
            document.getElementById('userInfo').textContent = 'Authenticated';
        }
    } catch (error) {
        console.error('Auth status check failed:', error);
    }
}

async function showAuthStatus() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE_URL}/auth/status/`, {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });

        const data = await response.json();
        console.log('Auth Status:', data);

        if (data.database_auth) {
            alert(`Authentication Status:\n\nMobile: ${data.database_auth.mobile}\nExpires: ${new Date(data.database_auth.expires_at).toLocaleString()}\nMethod: ${data.database_auth.login_method}`);
        } else {
            alert('Not authenticated');
        }
    } catch (error) {
        console.error('Failed to get auth status:', error);
        alert('Error getting authentication status');
    }
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE_URL}/statistics/`);
        const data = await response.json();

        const statsContent = document.getElementById('statisticsContent');
        statsContent.innerHTML = `
            <div class="stat-card">
                <h3>${data.total_channels}</h3>
                <p>Total Channels</p>
            </div>
            <div class="stat-card">
                <h3>${data.total_sessions}</h3>
                <p>Total Sessions</p>
            </div>
            <div class="stat-card">
                <h3>${data.most_viewed.length}</h3>
                <p>Most Viewed</p>
            </div>
        `;
    } catch (error) {
        console.error('Failed to load statistics:', error);
    }
}

// Refresh channels
async function refreshChannels() {
    showToast('Refreshing channels...', 'info');
    await loadTamilNewsChannels();
    await loadStatistics();
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Show modal message
function showMessage(message, type) {
    const messageEl = document.getElementById('authMessage');
    messageEl.textContent = message;
    messageEl.className = `message ${type}`;
}
