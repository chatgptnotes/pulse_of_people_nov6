# JioTV-Proxy Service

FastAPI-based proxy service for streaming JioTV channels, specifically optimized for Tamil news channels.

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start the service
docker-compose up -d

# Check logs
docker-compose logs -f jiotv-proxy

# Stop the service
docker-compose down
```

### Using Docker Only

```bash
# Build the image
docker build -t jiotv-proxy .

# Run the container
docker run -d -p 8000:8000 --name jiotv-proxy jiotv-proxy

# Check logs
docker logs -f jiotv-proxy
```

### Manual Setup (Without Docker)

```bash
# Clone JioTV-Proxy
git clone https://github.com/henry-richard7/JioTV-Proxy.git
cd JioTV-Proxy

# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py
```

## Authentication

### Login via Web UI
1. Open browser: http://localhost:8000/jiotv/login
2. Enter your Jio mobile number
3. Enter OTP received via SMS
4. You're authenticated!

### Login via API

```bash
# Send OTP
curl -X POST http://localhost:8000/login/sendOTP \
  -H "Content-Type: application/json" \
  -d '{"mobile": "91XXXXXXXXXX"}'

# Verify OTP
curl -X POST http://localhost:8000/login/verifyOTP \
  -H "Content-Type: application/json" \
  -d '{"mobile": "91XXXXXXXXXX", "otp": "XXXXXX"}'
```

## API Endpoints

### Get All Channels
```bash
curl http://localhost:8000/channels
```

### Get Tamil News Channels
```bash
curl http://localhost:8000/channels | jq '.[] | select(.language | contains("Tamil")) | select(.name | contains("News"))'
```

### Stream Channel
```bash
# Auto quality
curl http://localhost:8000/live/1561  # Sun News

# Specific quality
curl http://localhost:8000/live/high/1561  # Sun News HD
```

### Get M3U Playlist
```bash
curl http://localhost:8000/playlist.m3u > jiotv.m3u
```

## Tamil News Channels

| Channel Name           | Channel ID | Quality      |
|------------------------|------------|--------------|
| Sun News               | 1561       | SD/HD        |
| Puthiya Thalaimurai    | 1557       | SD/HD        |
| Thanthi TV             | 1559       | SD/HD        |
| News 7 Tamil           | 538        | SD           |
| Captain News           | 520        | SD           |
| Kalaignar Seithigal    | 526        | SD           |
| Raj News 24x7          | 1121       | SD           |

**Note**: Channel IDs may change. Always fetch fresh list via `/channels` endpoint.

## Quality Options

- `low` - 400 kbps
- `medium` - 600 kbps
- `high` - 800-1200 kbps
- `auto` - Adaptive bitrate

## Health Check

```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Service Not Starting
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill existing process
kill -9 <PID>
```

### Authentication Failed
- Ensure valid Jio mobile number
- Check OTP expiry (typically 5 minutes)
- Try password authentication if OTP fails

### Streams Not Playing
- Verify authentication token is valid
- Check channel ID is correct
- Ensure network connectivity
- Try different quality option

## Legal Disclaimer

⚠️ **IMPORTANT**: This is an unofficial reverse-engineered API.

- Use ONLY with your own valid Jio account
- For personal use ONLY
- NOT for commercial purposes
- NOT for content redistribution
- May violate JioTV Terms of Service
- Use at your own risk

## Support

For issues with:
- **JioTV-Proxy**: https://github.com/henry-richard7/JioTV-Proxy/issues
- **Django Integration**: Check backend API documentation

## Version

v1.0 - November 6, 2025
