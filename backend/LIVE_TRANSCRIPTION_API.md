# Live Speech-to-Text Transcription API Documentation

Complete API documentation for SarvamAI-powered live transcription service.

---

## Table of Contents
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [WebSocket API](#websocket-api)
- [REST API Endpoints](#rest-api-endpoints)
- [Implementation Summary](#implementation-summary)
- [Examples](#examples)

---

## Quick Start

### 1. Get Your JWT Token

**Endpoint:** `POST /api/auth/login/`

```bash
curl -X POST http://localhost:8080/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_email@example.com",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "your_email@example.com",
    "role": "user"
  }
}
```

### 2. Connect to WebSocket

**WebSocket URL:** `ws://localhost:8080/ws/transcribe/?token=YOUR_JWT_TOKEN`

**Production:** `wss://your-domain.com/ws/transcribe/?token=YOUR_JWT_TOKEN`

---

## Authentication

All API endpoints require JWT authentication.

### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

### Refresh Token
```http
POST /api/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Register New User
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123",
  "password_confirm": "password123"
}
```

---

## WebSocket API

### Connection

**URL:** `ws://localhost:8080/ws/transcribe/?token=JWT_TOKEN`

**Authentication:** JWT token in query parameter

### Message Protocol

#### 1. Client → Server: Config Message

Send this first after connection:

```json
{
  "type": "config",
  "language_code": "hi-IN"
}
```

**Supported Languages:**
- `hi-IN` - Hindi (हिन्दी)
- `en-IN` - English (India)
- `ta-IN` - Tamil (தமிழ்)
- `te-IN` - Telugu (తెలుగు)
- `kn-IN` - Kannada (ಕನ್ನಡ)
- `ml-IN` - Malayalam (മലയാളം)
- `mr-IN` - Marathi (मराठी)
- `bn-IN` - Bengali (বাংলা)
- `gu-IN` - Gujarati (ગુજરાતી)
- `pa-IN` - Punjabi (ਪੰਜਾਬੀ)

#### 2. Client → Server: Audio Data

Send audio chunks as base64:

```json
{
  "type": "audio",
  "data": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA..."
}
```

Or send raw binary audio bytes directly.

**Audio Specifications:**
- Format: WAV, MP3, or other common formats
- Sample Rate: 16kHz recommended
- Channels: Mono preferred
- Chunk Size: 1-2 seconds of audio

#### 3. Client → Server: End Signal

When done recording:

```json
{
  "type": "end"
}
```

#### 4. Server → Client: Connection Confirmed

```json
{
  "type": "connected",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Connected to transcription service"
}
```

#### 5. Server → Client: Config Confirmed

```json
{
  "type": "config_confirmed",
  "language_code": "hi-IN",
  "transcription_id": 123
}
```

#### 6. Server → Client: Partial Transcription

Received during streaming:

```json
{
  "type": "transcription",
  "text": "नमस्ते",
  "full_text": "नमस्ते आप कैसे हैं",
  "is_final": false
}
```

#### 7. Server → Client: Final Transcription

Received after sending "end":

```json
{
  "type": "final",
  "text": "नमस्ते आप कैसे हैं मैं ठीक हूँ धन्यवाद",
  "transcription_id": 123,
  "language_code": "hi-IN"
}
```

#### 8. Server → Client: Error

```json
{
  "type": "error",
  "message": "SarvamAI service not available"
}
```

### WebSocket Flow Diagram

```
Client                                  Server
  |                                       |
  |--- Connect with JWT token ---------->|
  |<-- {"type": "connected"} -------------|
  |                                       |
  |--- {"type": "config", ...} ---------->|
  |<-- {"type": "config_confirmed"} ------|
  |                                       |
  |--- {"type": "audio", ...} ----------->|
  |--- {"type": "audio", ...} ----------->|
  |<-- {"type": "transcription"} ---------|
  |--- {"type": "audio", ...} ----------->|
  |<-- {"type": "transcription"} ---------|
  |                                       |
  |--- {"type": "end"} ------------------>|
  |<-- {"type": "final"} -----------------|
  |                                       |
  |--- Close connection ----------------->|
```

---

## REST API Endpoints

Base URL: `http://localhost:8080/api`

All endpoints require `Authorization: Bearer JWT_TOKEN` header.

### 1. List Transcriptions

Get all transcriptions for the current user.

```http
GET /api/transcriptions/
Authorization: Bearer YOUR_JWT_TOKEN
```

**Query Parameters:**
- `status` (optional) - Filter by status: `pending`, `processing`, `completed`, `failed`
- `language` (optional) - Filter by language code: `hi-IN`, `en-IN`, etc.
- `search` (optional) - Search in transcription text

**Response:**
```json
{
  "count": 25,
  "next": "http://localhost:8080/api/transcriptions/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "username": "john@example.com",
      "language_code": "hi-IN",
      "language_name": "Hindi",
      "preview_text": "नमस्ते आप कैसे हैं मैं ठीक हूँ...",
      "status": "completed",
      "audio_duration": 15.5,
      "created_at": "2025-11-06T10:30:00Z",
      "completed_at": "2025-11-06T10:30:15Z"
    }
  ]
}
```

### 2. Get Transcription Details

Get full details of a specific transcription.

```http
GET /api/transcriptions/{id}/
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "id": 123,
  "user": 1,
  "username": "john@example.com",
  "language_code": "hi-IN",
  "language_name": "Hindi",
  "transcription_text": "नमस्ते आप कैसे हैं मैं ठीक हूँ धन्यवाद",
  "confidence_score": 0.95,
  "status": "completed",
  "status_display": "Completed",
  "error_message": "",
  "audio_metadata": {
    "format": "wav",
    "sample_rate": 16000,
    "channels": 1
  },
  "audio_duration": 15.5,
  "model_version": "saarika:v2.5",
  "sarvam_request_id": "req_abc123",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "started_at": "2025-11-06T10:30:00Z",
  "completed_at": "2025-11-06T10:30:15Z",
  "processing_time": 15.2,
  "created_at": "2025-11-06T10:30:00Z",
  "updated_at": "2025-11-06T10:30:15Z"
}
```

### 3. Delete Transcription

Delete a transcription record.

```http
DELETE /api/transcriptions/{id}/
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:** `204 No Content`

### 4. Get Supported Languages

List all supported languages.

```http
GET /api/transcriptions/languages/
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "languages": [
    {
      "code": "hi-IN",
      "name": "Hindi"
    },
    {
      "code": "en-IN",
      "name": "English (India)"
    },
    {
      "code": "ta-IN",
      "name": "Tamil"
    }
  ],
  "default": "hi-IN"
}
```

### 5. Get User Statistics

Get transcription statistics for current user.

```http
GET /api/transcriptions/stats/
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "total_transcriptions": 45,
  "completed": 42,
  "processing": 1,
  "failed": 2,
  "by_language": {
    "hi-IN": {
      "name": "Hindi",
      "count": 25
    },
    "en-IN": {
      "name": "English (India)",
      "count": 15
    },
    "ta-IN": {
      "name": "Tamil",
      "count": 5
    }
  },
  "total_duration": 1250.5
}
```

### 6. Export Transcription

Download transcription as plain text file.

```http
GET /api/transcriptions/{id}/export/
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:** Plain text file with transcription content

```
Content-Type: text/plain
Content-Disposition: attachment; filename="transcription_123.txt"

नमस्ते आप कैसे हैं मैं ठीक हूँ धन्यवाद
```

---

## Implementation Summary

### What Was Built

This implementation provides a complete live speech-to-text transcription system with the following components:

#### 1. Database Layer
- **Model:** `Transcription`
- **Fields:** user, language_code, transcription_text, status, audio_metadata, session_id, timestamps
- **Relationships:** Foreign key to User for multi-tenant isolation
- **Indexes:** Optimized queries on user, status, language, session_id

#### 2. WebSocket Infrastructure
- **Framework:** Django Channels 4.2.0
- **Server:** Daphne ASGI server
- **Authentication:** JWT-based WebSocket middleware
- **Consumer:** `TranscriptionConsumer` for real-time audio processing
- **Protocol:** Custom JSON-based message protocol

#### 3. SarvamAI Integration
- **Service:** `SarvamAIService` class
- **API:** HTTP REST API integration
- **Features:** Audio streaming, language selection, error handling
- **Models:** saarika:v2.5 (configurable)

#### 4. REST API
- **ViewSet:** `TranscriptionViewSet` with CRUD operations
- **Serializers:** Full and lightweight serializers for different use cases
- **Permissions:** IsAuthenticated - users can only see their own transcriptions
- **Pagination:** Page-based pagination with 10 items per page

#### 5. Security
- JWT token authentication for both HTTP and WebSocket
- User-scoped data access
- Row-level security (users see only their transcriptions)
- Secure WebSocket connections (wss:// in production)

### Architecture

```
┌─────────────┐
│   Client    │
│  (Browser/  │
│   Mobile)   │
└──────┬──────┘
       │
       │ WebSocket (JWT Auth)
       │
┌──────▼──────────────────────────────────┐
│         Django Channels                  │
│  ┌────────────────────────────────────┐ │
│  │  TranscriptionConsumer              │ │
│  │  - Receives audio chunks            │ │
│  │  - Buffers and processes            │ │
│  │  - Returns transcriptions           │ │
│  └────────┬───────────────────────────┘ │
└───────────┼──────────────────────────────┘
            │
            │ HTTP API Call
            │
┌───────────▼──────────────────────────────┐
│       SarvamAI Service                   │
│  - Audio format conversion               │
│  - API request handling                  │
│  - Response processing                   │
└───────────┬──────────────────────────────┘
            │
            │ HTTPS
            │
┌───────────▼──────────────────────────────┐
│       SarvamAI API                       │
│  - Speech-to-text processing             │
│  - Multi-language support                │
│  - Model: saarika:v2.5                   │
└──────────────────────────────────────────┘
```

### Files Structure

```
backend/
├── api/
│   ├── consumers/
│   │   ├── __init__.py
│   │   └── transcription_consumer.py       # WebSocket consumer
│   ├── middleware/
│   │   └── websocket_auth.py               # JWT WebSocket auth
│   ├── models.py                           # + Transcription model
│   ├── serializers.py                      # + Transcription serializers
│   ├── services/
│   │   └── sarvam_service.py               # SarvamAI integration
│   ├── views/
│   │   └── transcription_views.py          # REST API views
│   ├── urls/
│   │   └── __init__.py                     # + Transcription routes
│   └── routing.py                          # WebSocket URL routing
├── config/
│   ├── settings.py                         # + Channels config
│   └── asgi.py                             # + WebSocket routing
├── .env                                     # + SarvamAI API key
├── .env.example                             # + SarvamAI config template
├── requirements.txt                         # + Channels dependencies
├── LIVE_TRANSCRIPTION_API.md               # This file
└── WEBSOCKET_CLIENT_GUIDE.md               # Client examples
```

### Technologies Used

- **Backend Framework:** Django 5.2.7
- **Real-time:** Django Channels 4.2.0, Daphne
- **API Framework:** Django REST Framework 3.16.1
- **Authentication:** JWT (djangorestframework-simplejwt)
- **Database:** SQLite (dev), PostgreSQL (production)
- **Speech-to-Text:** SarvamAI API
- **WebSocket:** Native WebSocket with custom protocol
- **Channel Layer:** In-memory (dev), Redis (production)

### Configuration

**Environment Variables:**
```bash
# SarvamAI Configuration
SARVAM_AI_API_KEY=sk_7s8sqvgs_fKA3W9UrpSv65xmB1YurPMTx
SARVAM_AI_MODEL=saarika:v2.5

# Django Settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
USE_SQLITE=True

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## Examples

### JavaScript Client Example

```javascript
// Initialize WebSocket connection
const token = 'YOUR_JWT_TOKEN';
const ws = new WebSocket(`ws://localhost:8080/ws/transcribe/?token=${token}`);

// Handle connection
ws.onopen = () => {
    console.log('Connected to transcription service');

    // Send configuration
    ws.send(JSON.stringify({
        type: 'config',
        language_code: 'hi-IN'
    }));
};

// Handle messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch(data.type) {
        case 'connected':
            console.log('Session ID:', data.session_id);
            break;

        case 'config_confirmed':
            console.log('Config confirmed, transcription ID:', data.transcription_id);
            startRecording(); // Start sending audio
            break;

        case 'transcription':
            console.log('Partial:', data.full_text);
            updateUI(data.full_text);
            break;

        case 'final':
            console.log('Final transcription:', data.text);
            console.log('Saved as ID:', data.transcription_id);
            stopRecording();
            break;

        case 'error':
            console.error('Error:', data.message);
            break;
    }
};

// Send audio chunk
function sendAudioChunk(audioData) {
    const base64Audio = btoa(String.fromCharCode(...new Uint8Array(audioData)));

    ws.send(JSON.stringify({
        type: 'audio',
        data: base64Audio
    }));
}

// End transcription
function endTranscription() {
    ws.send(JSON.stringify({
        type: 'end'
    }));
}
```

### Python Client Example

```python
import asyncio
import websockets
import json

async def transcribe():
    token = 'YOUR_JWT_TOKEN'
    uri = f'ws://localhost:8080/ws/transcribe/?token={token}'

    async with websockets.connect(uri) as websocket:
        # Send config
        await websocket.send(json.dumps({
            'type': 'config',
            'language_code': 'hi-IN'
        }))

        # Receive config confirmation
        response = await websocket.recv()
        print(f'Config: {response}')

        # Send audio chunks
        for audio_chunk in get_audio_chunks():
            await websocket.send(json.dumps({
                'type': 'audio',
                'data': audio_chunk
            }))

            # Receive partial transcription
            response = await websocket.recv()
            data = json.loads(response)
            if data['type'] == 'transcription':
                print(f"Partial: {data['full_text']}")

        # End transcription
        await websocket.send(json.dumps({'type': 'end'}))

        # Receive final transcription
        final = await websocket.recv()
        print(f'Final: {final}')

asyncio.run(transcribe())
```

### cURL Examples

```bash
# Get supported languages
curl -X GET http://localhost:8080/api/transcriptions/languages/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# List all transcriptions
curl -X GET http://localhost:8080/api/transcriptions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Filter by status
curl -X GET "http://localhost:8080/api/transcriptions/?status=completed" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Search in transcriptions
curl -X GET "http://localhost:8080/api/transcriptions/?search=नमस्ते" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get transcription details
curl -X GET http://localhost:8080/api/transcriptions/123/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get user statistics
curl -X GET http://localhost:8080/api/transcriptions/stats/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Export transcription
curl -X GET http://localhost:8080/api/transcriptions/123/export/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -o transcription.txt

# Delete transcription
curl -X DELETE http://localhost:8080/api/transcriptions/123/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Error Codes

| HTTP Code | Meaning |
|-----------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful deletion) |
| 400 | Bad Request (invalid data) |
| 401 | Unauthorized (invalid or missing token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 405 | Method Not Allowed |
| 500 | Internal Server Error |

### WebSocket Close Codes

| Code | Meaning |
|------|---------|
| 1000 | Normal closure |
| 4001 | Unauthorized (invalid token) |
| 4003 | Forbidden |

---

## Rate Limits

- **Anonymous requests:** 100/hour
- **Authenticated requests:** 1000/hour
- **WebSocket connections:** No limit

---

## Best Practices

1. **Always close WebSocket connections** when done
2. **Implement reconnection logic** for network issues
3. **Buffer audio chunks** to ~1-2 seconds before sending
4. **Handle errors gracefully** on client side
5. **Use refresh tokens** to maintain long sessions
6. **Clean up audio streams** after recording
7. **Use wss://** in production for secure connections

---

## Support & Contact

- **Documentation:** See `WEBSOCKET_CLIENT_GUIDE.md` for detailed client examples
- **Issues:** Report bugs via GitHub
- **Email:** support@pulseofpeople.com

---

**API Version:** 1.0
**Last Updated:** 2025-11-06
**Server:** Django 5.2.7 + Channels 4.2.0
**Speech-to-Text:** SarvamAI saarika:v2.5
