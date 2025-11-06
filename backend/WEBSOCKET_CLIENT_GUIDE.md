# WebSocket Speech-to-Text Client Guide

Complete guide for integrating live speech-to-text transcription using WebSockets with SarvamAI.

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [WebSocket Connection](#websocket-connection)
- [Message Protocol](#message-protocol)
- [JavaScript Example](#javascript-example)
- [Python Example](#python-example)
- [REST API Endpoints](#rest-api-endpoints)
- [Troubleshooting](#troubleshooting)

## Overview

The live transcription service uses WebSocket for real-time bidirectional communication between client and server. Audio is streamed to the server, processed by SarvamAI, and transcriptions are sent back in real-time.

**Features:**
- Real-time audio streaming
- Support for 10 Indian languages
- Automatic transcription storage
- Session management
- Partial and final results

## Authentication

WebSocket connections require JWT authentication via query parameters.

### Get JWT Token

First, login to get your access token:

```bash
curl -X POST http://localhost:8080/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_email@example.com",
    "password": "your_password"
  }'
```

Response:
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

## WebSocket Connection

**Endpoint:** `ws://localhost:8080/ws/transcribe/?token=YOUR_JWT_TOKEN`

**Production:** `wss://your-domain.com/ws/transcribe/?token=YOUR_JWT_TOKEN`

## Message Protocol

### Client → Server Messages

#### 1. Config Message (Required First)
```json
{
  "type": "config",
  "language_code": "hi-IN"
}
```

**Supported Languages:**
- `hi-IN` - Hindi
- `en-IN` - English (India)
- `ta-IN` - Tamil
- `te-IN` - Telugu
- `kn-IN` - Kannada
- `ml-IN` - Malayalam
- `mr-IN` - Marathi
- `bn-IN` - Bengali
- `gu-IN` - Gujarati
- `pa-IN` - Punjabi

#### 2. Audio Message
```json
{
  "type": "audio",
  "data": "<base64_encoded_audio>"
}
```

Or send raw binary audio bytes directly.

#### 3. End Message
```json
{
  "type": "end"
}
```

### Server → Client Messages

#### 1. Connected
```json
{
  "type": "connected",
  "session_id": "uuid-here",
  "message": "Connected to transcription service"
}
```

#### 2. Config Confirmed
```json
{
  "type": "config_confirmed",
  "language_code": "hi-IN",
  "transcription_id": 123
}
```

#### 3. Partial Transcription
```json
{
  "type": "transcription",
  "text": "नमस्ते",
  "full_text": "नमस्ते आप कैसे हैं",
  "is_final": false
}
```

#### 4. Final Transcription
```json
{
  "type": "final",
  "text": "नमस्ते आप कैसे हैं मैं ठीक हूँ",
  "transcription_id": 123,
  "language_code": "hi-IN"
}
```

#### 5. Error
```json
{
  "type": "error",
  "message": "Error description"
}
```

## JavaScript Example

### HTML + JavaScript Client

```html
<!DOCTYPE html>
<html>
<head>
    <title>Live Transcription Demo</title>
</head>
<body>
    <h1>Live Speech-to-Text</h1>

    <select id="languageSelect">
        <option value="hi-IN">Hindi</option>
        <option value="en-IN">English</option>
        <option value="ta-IN">Tamil</option>
        <option value="te-IN">Telugu</option>
    </select>

    <button id="startBtn">Start Recording</button>
    <button id="stopBtn" disabled>Stop</button>

    <div id="transcription"></div>

    <script>
        const JWT_TOKEN = 'YOUR_JWT_TOKEN_HERE';
        const WS_URL = `ws://localhost:8080/ws/transcribe/?token=${JWT_TOKEN}`;

        let websocket = null;
        let mediaRecorder = null;
        let audioChunks = [];

        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const languageSelect = document.getElementById('languageSelect');
        const transcriptionDiv = document.getElementById('transcription');

        // Connect to WebSocket
        function connectWebSocket() {
            websocket = new WebSocket(WS_URL);

            websocket.onopen = () => {
                console.log('WebSocket connected');

                // Send config
                const config = {
                    type: 'config',
                    language_code: languageSelect.value
                };
                websocket.send(JSON.stringify(config));
            };

            websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('Received:', data);

                if (data.type === 'transcription') {
                    transcriptionDiv.innerHTML = `<p><strong>Transcription:</strong> ${data.full_text}</p>`;
                } else if (data.type === 'final') {
                    transcriptionDiv.innerHTML += `<p><strong>Final:</strong> ${data.text}</p>`;
                    transcriptionDiv.innerHTML += `<p><em>Saved as ID: ${data.transcription_id}</em></p>`;
                } else if (data.type === 'error') {
                    transcriptionDiv.innerHTML += `<p style="color: red;"><strong>Error:</strong> ${data.message}</p>`;
                }
            };

            websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                transcriptionDiv.innerHTML += `<p style="color: red;">Connection error</p>`;
            };

            websocket.onclose = () => {
                console.log('WebSocket disconnected');
            };
        }

        // Start recording
        startBtn.addEventListener('click', async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);

                    // Send audio chunk to server
                    const reader = new FileReader();
                    reader.onload = () => {
                        const base64Audio = btoa(String.fromCharCode(...new Uint8Array(reader.result)));

                        if (websocket && websocket.readyState === WebSocket.OPEN) {
                            websocket.send(JSON.stringify({
                                type: 'audio',
                                data: base64Audio
                            }));
                        }
                    };
                    reader.readAsArrayBuffer(event.data);
                };

                connectWebSocket();
                mediaRecorder.start(1000); // Send chunks every second

                startBtn.disabled = true;
                stopBtn.disabled = false;
                transcriptionDiv.innerHTML = '<p>Recording...</p>';

            } catch (error) {
                console.error('Error accessing microphone:', error);
                alert('Could not access microphone');
            }
        });

        // Stop recording
        stopBtn.addEventListener('click', () => {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();

                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }

            if (websocket) {
                websocket.send(JSON.stringify({ type: 'end' }));
                websocket.close();
            }

            startBtn.disabled = false;
            stopBtn.disabled = true;
        });
    </script>
</body>
</html>
```

## Python Example

```python
import asyncio
import websockets
import json
import pyaudio
import base64

JWT_TOKEN = 'YOUR_JWT_TOKEN_HERE'
WS_URL = f'ws://localhost:8080/ws/transcribe/?token={JWT_TOKEN}'

async def transcribe_audio():
    # Connect to WebSocket
    async with websockets.connect(WS_URL) as websocket:
        # Send config
        config = {
            'type': 'config',
            'language_code': 'hi-IN'
        }
        await websocket.send(json.dumps(config))

        # Receive config confirmation
        response = await websocket.recv()
        print('Config response:', response)

        # Setup audio recording
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000

        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        print("Recording... Press Ctrl+C to stop")

        try:
            # Create tasks for sending and receiving
            send_task = asyncio.create_task(send_audio(websocket, stream, CHUNK))
            receive_task = asyncio.create_task(receive_transcriptions(websocket))

            # Run both tasks
            await asyncio.gather(send_task, receive_task)

        except KeyboardInterrupt:
            print("\nStopping...")

        finally:
            # Cleanup
            stream.stop_stream()
            stream.close()
            p.terminate()

            # Send end signal
            await websocket.send(json.dumps({'type': 'end'}))

            # Wait for final response
            final = await websocket.recv()
            print('Final:', final)

async def send_audio(websocket, stream, chunk_size):
    while True:
        try:
            # Read audio data
            data = stream.read(chunk_size, exception_on_overflow=False)

            # Encode to base64
            audio_base64 = base64.b64encode(data).decode('utf-8')

            # Send to server
            message = {
                'type': 'audio',
                'data': audio_base64
            }
            await websocket.send(json.dumps(message))

            await asyncio.sleep(0.1)

        except Exception as e:
            print(f'Send error: {e}')
            break

async def receive_transcriptions(websocket):
    while True:
        try:
            response = await websocket.recv()
            data = json.loads(response)

            if data['type'] == 'transcription':
                print(f"\rTranscription: {data['full_text']}", end='', flush=True)
            elif data['type'] == 'final':
                print(f"\n\nFinal: {data['text']}")
                print(f"Saved as ID: {data['transcription_id']}")
                break
            elif data['type'] == 'error':
                print(f"\nError: {data['message']}")
                break

        except Exception as e:
            print(f'Receive error: {e}')
            break

# Run
if __name__ == '__main__':
    asyncio.run(transcribe_audio())
```

## REST API Endpoints

### List Transcriptions
```bash
GET /api/transcriptions/
Authorization: Bearer YOUR_JWT_TOKEN
```

**Query Parameters:**
- `status` - Filter by status (pending, processing, completed, failed)
- `language` - Filter by language code
- `search` - Search in transcription text

### Get Transcription Details
```bash
GET /api/transcriptions/{id}/
Authorization: Bearer YOUR_JWT_TOKEN
```

### Delete Transcription
```bash
DELETE /api/transcriptions/{id}/
Authorization: Bearer YOUR_JWT_TOKEN
```

### Get Supported Languages
```bash
GET /api/transcriptions/languages/
Authorization: Bearer YOUR_JWT_TOKEN
```

### Get Statistics
```bash
GET /api/transcriptions/stats/
Authorization: Bearer YOUR_JWT_TOKEN
```

### Export Transcription
```bash
GET /api/transcriptions/{id}/export/
Authorization: Bearer YOUR_JWT_TOKEN
```

## Troubleshooting

### Connection Issues

**Error: WebSocket connection failed**
- Check JWT token is valid and not expired
- Verify WebSocket URL format: `ws://` for local, `wss://` for production
- Ensure server is running and accessible

**Error: Authentication failed**
- Token might be expired - get new token via `/api/auth/refresh/`
- Check token is included in query params: `?token=YOUR_TOKEN`

### Audio Issues

**No transcription received**
- Check audio format is supported (WAV, MP3, etc.)
- Verify microphone permissions
- Check audio chunk size (recommended: 1024 bytes)
- Ensure sample rate is 16kHz or higher

**Poor transcription quality**
- Use better quality microphone
- Reduce background noise
- Speak clearly and at moderate pace
- Select correct language code

### Server Issues

**Error: SarvamAI service not available**
- Check `SARVAM_AI_API_KEY` is configured in `.env`
- Verify API key is valid
- Check SarvamAI API status

## Best Practices

1. **Audio Quality**
   - Use 16kHz sample rate minimum
   - Mono channel preferred
   - WAV format for best results

2. **Network**
   - Use WebSocket reconnection logic
   - Handle disconnections gracefully
   - Buffer audio during connection issues

3. **Security**
   - Always use `wss://` in production
   - Keep JWT tokens secure
   - Implement token refresh logic
   - Don't hardcode credentials

4. **Performance**
   - Send audio chunks every 1-2 seconds
   - Don't send chunks too small (<500ms)
   - Close connection when done
   - Clean up resources properly

## Support

For issues:
- Check server logs: `docker logs backend`
- Enable debug mode in Django settings
- Contact: support@pulseofpeople.com

---

**Version:** 1.0
**Last Updated:** 2025-11-06
**License:** MIT
