# JioTV Tamil News Channels - Complete Setup Guide

A comprehensive integration of JioTV API for streaming Tamil news channels (Sun News, Puthiya Thalaimurai, Thanthi TV, News 7 Tamil, etc.) in your Django backend with a modern web player.

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [Detailed Setup](#detailed-setup)
6. [API Documentation](#api-documentation)
7. [Frontend Usage](#frontend-usage)
8. [Troubleshooting](#troubleshooting)
9. [Legal Disclaimer](#legal-disclaimer)

---

## Features

- **Tamil News Channels**: Stream popular Tamil news channels
- **Multiple Quality Options**: Low, Medium, High, and Auto adaptive streaming
- **Modern Web Player**: HTML5 video player with HLS.js support
- **User Authentication**: OTP and password-based JioTV authentication
- **Channel Management**: Browse, search, and favorite channels
- **Session Tracking**: Monitor user streaming sessions
- **Statistics Dashboard**: View most watched channels and analytics
- **M3U Playlist**: Generate playlists for IPTV players
- **RESTful API**: Complete API for integration with any frontend

---

## Architecture

```
┌─────────────┐
│   Browser   │
│  (Player)   │
└──────┬──────┘
       │ HTTPS
┌──────▼────────────┐
│  Django Backend   │
│  ┌─────────────┐  │
│  │ JioTV       │  │
│  │ Service     │  │
│  │ Layer       │  │
│  └──────┬──────┘  │
└─────────┼─────────┘
          │ HTTP
┌─────────▼─────────┐
│  JioTV-Proxy      │
│  (FastAPI/Docker) │
└─────────┬─────────┘
          │ HTTPS
┌─────────▼─────────┐
│  JioTV Official   │
│  API Servers      │
└───────────────────┘
```

---

## Prerequisites

### System Requirements
- Python 3.10+
- Django 5.2+
- Docker & Docker Compose (recommended)
- Redis (optional, for caching)
- Node.js (for frontend development)

### Required Accounts
- Jio account with valid mobile number
- Active Jio subscription (if premium channels required)

---

## Quick Start

### 1. Start JioTV-Proxy Service

```bash
cd backend/jiotv-proxy
docker-compose up -d
```

Or manually:
```bash
git clone https://github.com/henry-richard7/JioTV-Proxy.git
cd JioTV-Proxy
pip install -r requirements.txt
python main.py
```

### 2. Configure Django Backend

```bash
cd backend

# Copy environment file
cp .env.example .env

# Edit .env and set:
# JIOTV_API_URL=http://localhost:8000

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start Django server
python manage.py runserver 8080
```

### 3. Open Frontend

```bash
# Open in browser
open frontend/jiotv.html

# Or serve with Python
cd frontend
python -m http.server 3000
# Then visit: http://localhost:3000/jiotv.html
```

### 4. Authenticate

1. Click "Login" button in the web player
2. Choose authentication method:
   - **OTP**: Enter mobile number → Receive OTP → Verify
   - **Password**: Enter mobile number and password
3. Start watching channels!

---

## Detailed Setup

### Step 1: Database Setup

Run Django migrations to create JioTV models:

```bash
python manage.py makemigrations api
python manage.py migrate
```

This creates:
- `TVChannel` - Stores channel information
- `StreamSession` - Tracks user viewing sessions
- `JioTVAuthentication` - Stores authentication tokens

### Step 2: Register Models in Admin

```python
# backend/api/admin.py
from api.models import TVChannel, StreamSession, JioTVAuthentication

@admin.register(TVChannel)
class TVChannelAdmin(admin.ModelAdmin):
    list_display = ['channel_id', 'name', 'language', 'category', 'view_count']
    list_filter = ['language', 'category', 'is_active']
    search_fields = ['name', 'channel_id']

@admin.register(StreamSession)
class StreamSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'channel', 'status', 'started_at', 'duration_seconds']
    list_filter = ['status', 'started_at']

@admin.register(JioTVAuthentication)
class JioTVAuthenticationAdmin(admin.ModelAdmin):
    list_display = ['mobile_number', 'is_active', 'token_created_at', 'token_expires_at']
    list_filter = ['is_active', 'login_method']
```

### Step 3: Configure Cache (Optional but Recommended)

For production, use Redis for caching:

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Step 4: Environment Variables

Update `.env`:

```env
# JioTV Configuration
JIOTV_API_URL=http://localhost:8000
JIOTV_CACHE_TIMEOUT=21600  # 6 hours
JIOTV_TOKEN_EXPIRY=82800   # 23 hours

# Optional: Auto-login credentials
JIOTV_MOBILE=91XXXXXXXXXX
JIOTV_PASSWORD=your_password
```

---

## API Documentation

### Base URL
```
http://localhost:8080/api/jiotv/
```

### Authentication Endpoints

#### 1. Check Service Health
```http
GET /health/
```

Response:
```json
{
  "status": "online",
  "status_code": 200,
  "timestamp": "2025-11-06T10:00:00Z"
}
```

#### 2. Send OTP
```http
POST /auth/send-otp/
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "mobile": "91XXXXXXXXXX"
}
```

Response:
```json
{
  "success": true,
  "message": "OTP sent successfully"
}
```

#### 3. Verify OTP
```http
POST /auth/verify-otp/
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "mobile": "91XXXXXXXXXX",
  "otp": "123456"
}
```

Response:
```json
{
  "success": true,
  "message": "Authentication successful",
  "expires_at": "2025-11-07T09:00:00Z"
}
```

#### 4. Login with Password
```http
POST /auth/password/
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "mobile": "91XXXXXXXXXX",
  "password": "your_password"
}
```

#### 5. Check Auth Status
```http
GET /auth/status/
Authorization: Bearer <access_token>
```

### Channel Endpoints

#### 1. Get Tamil News Channels
```http
GET /channels/tamil-news/
```

Response:
```json
{
  "count": 7,
  "channels": [
    {
      "id": "1561",
      "name": "Sun News",
      "logoUrl": "https://...",
      "language": "Tamil",
      "category": "News",
      "isHD": false
    },
    ...
  ],
  "timestamp": "2025-11-06T10:00:00Z"
}
```

#### 2. Get All Channels
```http
GET /channels/all/
```

#### 3. Get Channel Details
```http
GET /channels/{channel_id}/
```

Response:
```json
{
  "id": "1561",
  "name": "Sun News",
  "logoUrl": "https://...",
  "language": "Tamil",
  "category": "News",
  "stream_urls": {
    "low": "http://localhost:8000/live/low/1561",
    "medium": "http://localhost:8000/live/medium/1561",
    "high": "http://localhost:8000/live/high/1561",
    "auto": "http://localhost:8000/live/1561"
  }
}
```

### Streaming Endpoints

#### 1. Get Stream URL
```http
GET /stream/{channel_id}/?quality=high
Authorization: Bearer <access_token>
```

Response:
```json
{
  "channel_id": "1561",
  "stream_url": "http://localhost:8000/live/high/1561",
  "quality": "high",
  "timestamp": "2025-11-06T10:00:00Z"
}
```

#### 2. End Stream Session
```http
POST /stream/session/{session_id}/end/
Authorization: Bearer <access_token>
```

### Playlist Endpoints

#### 1. Get M3U Playlist
```http
GET /playlist/?tamil_only=true
```

Returns M3U8 playlist file for IPTV players.

### Analytics Endpoints

#### 1. Get Statistics
```http
GET /statistics/
```

Response:
```json
{
  "most_viewed": [
    {
      "channel_id": "1561",
      "name": "Sun News",
      "view_count": 1250,
      "logo_url": "https://..."
    }
  ],
  "recently_viewed": [...],
  "total_channels": 7,
  "total_sessions": 3420
}
```

#### 2. Get User History
```http
GET /history/
Authorization: Bearer <access_token>
```

---

## Frontend Usage

### Basic Integration

```html
<!DOCTYPE html>
<html>
<head>
    <title>JioTV Player</title>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
</head>
<body>
    <video id="player" controls width="100%"></video>

    <script>
        const API_URL = 'http://localhost:8080/api/jiotv';

        async function playChannel(channelId, quality = 'auto') {
            const response = await fetch(
                `${API_URL}/stream/${channelId}/?quality=${quality}`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            const data = await response.json();
            const streamUrl = data.stream_url;

            // Initialize HLS player
            const video = document.getElementById('player');
            if (Hls.isSupported()) {
                const hls = new Hls();
                hls.loadSource(streamUrl);
                hls.attachMedia(video);
                hls.on(Hls.Events.MANIFEST_PARSED, () => {
                    video.play();
                });
            }
        }

        // Play Sun News
        playChannel('1561', 'high');
    </script>
</body>
</html>
```

### Using the Provided Web Player

The frontend includes a complete web player at `frontend/jiotv.html`:

1. **Features**:
   - Channel browsing grid
   - Quality selector (Auto, High, Medium, Low)
   - Authentication modal
   - Statistics dashboard
   - Responsive design

2. **Customization**:
   ```javascript
   // Edit js/jiotv-player.js
   const API_BASE_URL = 'https://your-domain.com/api/jiotv';
   ```

3. **Styling**:
   ```css
   /* Edit css/jiotv-player.css */
   :root {
       --primary-color: #1e88e5;
       /* Customize colors */
   }
   ```

---

## Troubleshooting

### Problem: JioTV-Proxy Service Not Starting

**Solution**:
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill existing process
kill -9 <PID>

# Check Docker logs
docker-compose logs -f jiotv-proxy
```

### Problem: Authentication Failed

**Possible Causes**:
1. Invalid mobile number format (must include country code: 91XXXXXXXXXX)
2. Expired OTP (valid for 5 minutes)
3. Incorrect password
4. Account not active

**Solution**:
- Verify mobile number format
- Request new OTP
- Check Jio account status
- Try password authentication instead

### Problem: Stream Not Playing

**Possible Causes**:
1. Authentication token expired
2. Channel ID incorrect
3. Network issues
4. CORS errors

**Solution**:
```javascript
// Check browser console for errors
// Verify authentication
const response = await fetch(`${API_URL}/auth/status/`);

// Check stream URL accessibility
fetch(streamUrl)
    .then(res => console.log('Stream accessible:', res.ok))
    .catch(err => console.error('Stream error:', err));
```

### Problem: CORS Errors

**Solution**:
```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

CORS_ALLOW_CREDENTIALS = True
```

### Problem: HLS.js Not Working

**Solution**:
1. Check browser compatibility (Chrome, Firefox, Edge supported)
2. For Safari, use native HLS:
   ```javascript
   if (video.canPlayType('application/vnd.apple.mpegurl')) {
       video.src = streamUrl;
   }
   ```

---

## Production Deployment

### 1. Use HTTPS

```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    location /api/jiotv/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Use Redis for Caching

```bash
# Install Redis
sudo apt install redis-server

# Start Redis
sudo systemctl start redis
```

### 3. Use Gunicorn

```bash
# Install
pip install gunicorn

# Run
gunicorn config.wsgi:application --bind 0.0.0.0:8080 --workers 4
```

### 4. Set Environment Variables

```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## Tamil News Channels List

| Channel Name           | Channel ID | Language | Category |
|------------------------|------------|----------|----------|
| Sun News               | 1561       | Tamil    | News     |
| Puthiya Thalaimurai    | 1557       | Tamil    | News     |
| Thanthi TV             | 1559       | Tamil    | News     |
| News 7 Tamil           | 538        | Tamil    | News     |
| Captain News           | 520        | Tamil    | News     |
| Kalaignar Seithigal    | 526        | Tamil    | News     |
| Raj News 24x7          | 1121       | Tamil    | News     |

**Note**: Channel IDs may change. Always fetch the latest list from `/channels/tamil-news/` endpoint.

---

## Legal Disclaimer

**IMPORTANT**: This is an **unofficial, reverse-engineered API integration**.

### Terms of Use

- ✅ Use ONLY with your own valid Jio account
- ✅ For personal use ONLY
- ✅ Educational purposes
- ❌ NOT for commercial purposes
- ❌ NOT for content redistribution
- ❌ NOT for creating competing services
- ❌ NOT for public streaming services

### Legal Considerations

1. **Terms of Service**: May violate JioTV's Terms of Service
2. **Copyright**: All content is copyrighted by respective channels
3. **Personal Use**: Generally acceptable for personal viewing with valid subscription
4. **Commercial Use**: Absolutely prohibited without proper licensing
5. **Liability**: Use at your own risk

### Recommendations

- **For Personal Learning**: OK with caution
- **For Production/Commercial**: NOT RECOMMENDED
- **For Startups**: Seek official partnerships with Jio
- **For Commercial Projects**: Contact Jio for official API access and licensing

---

## Support & Contributing

### Issues

For issues related to:
- **JioTV-Proxy**: https://github.com/henry-richard7/JioTV-Proxy/issues
- **Django Integration**: Create an issue in your project repository

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Contact

For questions or support, please open an issue in the project repository.

---

## Version History

**v1.0 - November 6, 2025**
- Initial release
- Django backend integration
- Modern web player
- Tamil news channels support
- Multiple quality options
- Authentication system
- Statistics dashboard

---

## FAQ

### Q: Do I need a Jio subscription?
**A**: Yes, you need a valid Jio account with an active subscription.

### Q: Can I use this for commercial purposes?
**A**: No, this is for personal use only. Contact Jio for commercial licensing.

### Q: Why are some channels not working?
**A**: Some channels (especially Sony channels) may be restricted. Channel availability depends on your Jio subscription.

### Q: How long does authentication last?
**A**: Tokens are valid for approximately 24 hours, then need to be refreshed.

### Q: Can I use this outside India?
**A**: JioTV services are primarily for India. VPN usage may violate terms of service.

### Q: Is this safe to use?
**A**: Use with your own account for personal viewing is generally safe, but it's an unofficial integration.

---

**Version**: 1.0
**Last Updated**: November 6, 2025
**Maintained By**: Your Team

---

For more information, visit the [JioTV-Proxy GitHub Repository](https://github.com/henry-richard7/JioTV-Proxy).
