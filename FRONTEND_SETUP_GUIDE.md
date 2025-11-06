# Frontend Setup & Testing Guide

## Quick Start - Testing the Application

### Step 1: Start the Backend Server

The Django backend is already running on port 8080. If it's not running:

```bash
cd /Users/apple/Downloads/pulseofpeople_Django-main/backend
source venv/bin/activate
python manage.py runserver 8080
```

You should see: `Starting development server at http://127.0.0.1:8080/`

### Step 2: Open the Frontend

You have two options:

#### Option A: Direct File Open (Simple)
```bash
open /Users/apple/Downloads/pulseofpeople_Django-main/frontend/index.html
```

#### Option B: Local HTTP Server (Recommended)
```bash
cd /Users/apple/Downloads/pulseofpeople_Django-main/frontend
python -m http.server 3000
```

Then open your browser to: **http://localhost:3000**

### Step 3: Create a Test User (If Needed)

If you don't have a user account yet:

```bash
cd backend
source venv/bin/activate
python manage.py createsuperuser
```

Follow the prompts to create username and password.

### Step 4: Test the Application

1. **Login**: Use your Django credentials
2. **Select Language**: Choose from the dropdown (default: Hindi)
3. **Start Recording**: Click the green "Start Recording" button
4. **Speak**: Say something in your selected language
5. **See Live Transcription**: Text appears in real-time
6. **Stop Recording**: Click the red "Stop Recording" button
7. **View History**: See your saved transcriptions below

## What's Been Built

### Complete Frontend Application

```
frontend/
├── index.html              # Main application page
├── css/
│   └── styles.css          # Professional responsive design
├── js/
│   ├── app.js              # Main application orchestrator
│   ├── auth.js             # JWT authentication
│   ├── api.js              # REST API client
│   ├── websocket.js        # WebSocket client for live streaming
│   ├── audio.js            # Microphone recording with MediaRecorder
│   └── ui.js               # DOM manipulation and updates
└── README.md               # Detailed documentation
```

### Key Features Implemented

1. **User Authentication**
   - Login/logout with JWT tokens
   - Auto-refresh expired tokens
   - Secure session management

2. **Live Transcription**
   - Real-time audio streaming via WebSocket
   - 10 Indian languages supported
   - Live text updates as you speak
   - Auto-saves to database

3. **History Management**
   - View all past transcriptions
   - Search by text content
   - Filter by status and language
   - Pagination for large datasets

4. **Export & Delete**
   - Export transcriptions as .txt files
   - Delete unwanted transcriptions
   - View detailed transcription info

5. **Statistics Dashboard**
   - Total transcriptions count
   - Completed vs failed status
   - Total duration tracked

## Testing Checklist

### 1. Authentication Test
- [ ] Open the application
- [ ] Login form appears
- [ ] Enter valid credentials
- [ ] Login successful, redirected to main app
- [ ] User email displayed in header

### 2. Recording Test
- [ ] Select language from dropdown
- [ ] Click "Start Recording"
- [ ] Browser asks for microphone permission
- [ ] Allow microphone access
- [ ] Connection status shows "Connected"
- [ ] Speak in selected language
- [ ] Live transcription appears in real-time
- [ ] Click "Stop Recording"
- [ ] Final transcription saved

### 3. History Test
- [ ] Transcription appears in history list
- [ ] Click eye icon to view details
- [ ] Modal shows complete transcription
- [ ] Close modal works
- [ ] Click download icon to export
- [ ] File downloads successfully

### 4. Filter & Search Test
- [ ] Type in search box
- [ ] Results filter in real-time
- [ ] Select status filter
- [ ] Results update accordingly
- [ ] Select language filter
- [ ] Results show only selected language

### 5. Statistics Test
- [ ] Statistics cards show correct counts
- [ ] Total transcriptions increments after recording
- [ ] Completed count updates
- [ ] Duration shows in minutes

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Browser)                       │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐  │
│  │  app.js  │  │ audio.js │  │websocket.js│  │  api.js  │  │
│  │ (Main)   │  │(MediaRec)│  │ (WS Client)│  │(REST API)│  │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘  └────┬─────┘  │
│       │             │               │              │         │
│       └─────────────┴───────────────┴──────────────┘         │
│                         │                                     │
└─────────────────────────┼─────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 Backend (Django + Channels)                  │
│                                                               │
│  ┌──────────────┐         ┌─────────────────────────────┐   │
│  │  REST API    │         │   WebSocket Consumer        │   │
│  │  (DRF)       │         │   (Channels)                │   │
│  │              │         │                             │   │
│  │ - Login      │         │ - Receive audio chunks      │   │
│  │ - History    │         │ - Stream to SarvamAI        │   │
│  │ - Stats      │         │ - Send back transcriptions  │   │
│  │ - Export     │         │ - Save to database          │   │
│  └──────┬───────┘         └────────┬────────────────────┘   │
│         │                          │                         │
│         └──────────┬───────────────┘                         │
│                    │                                         │
│         ┌──────────▼──────────┐                              │
│         │   Database          │                              │
│         │   (PostgreSQL)      │                              │
│         │                     │                              │
│         │ - Users             │                              │
│         │ - Transcriptions    │                              │
│         └─────────────────────┘                              │
│                    │                                         │
└────────────────────┼─────────────────────────────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │  SarvamAI   │
              │  API        │
              │             │
              │ saarika:v2.5│
              └─────────────┘
```

## API Endpoints Reference

### Authentication
```
POST /api/auth/login/
POST /api/auth/refresh/
```

### Transcriptions
```
GET    /api/transcriptions/              # List all
GET    /api/transcriptions/{id}/         # Get one
DELETE /api/transcriptions/{id}/         # Delete
GET    /api/transcriptions/stats/        # Statistics
GET    /api/transcriptions/languages/    # Languages list
GET    /api/transcriptions/{id}/export/  # Export as text
```

### WebSocket
```
ws://localhost:8080/ws/transcribe/?token={JWT_TOKEN}
```

## Workflow Diagram

```
User Opens App
     │
     ▼
Login with Credentials
     │
     ▼
Main Dashboard Loads
     │
     ├─► Statistics Fetched (REST API)
     ├─► History Loaded (REST API)
     └─► Languages Populated
          │
          ▼
     User Selects Language
          │
          ▼
     Click "Start Recording"
          │
          ├─► WebSocket Connection Opens
          ├─► Send Config (language_code)
          ├─► Receive Transcription ID
          ├─► Start Audio Recording
          │    │
          │    ├─► Capture 1-second chunks
          │    ├─► Convert to base64
          │    └─► Send via WebSocket
          │         │
          │         ▼
          │    Backend receives audio
          │         │
          │         ├─► Forward to SarvamAI
          │         ├─► Receive transcription
          │         └─► Send back to client
          │              │
          │              ▼
          │         Live text updates
          │
          ▼
     Click "Stop Recording"
          │
          ├─► Send 'end' signal
          ├─► Stop audio recording
          ├─► Backend finalizes
          ├─► Save to database
          └─► Send final transcription
               │
               ▼
          Update history
          Update statistics
```

## Troubleshooting

### Problem: "Microphone access denied"
**Solution**:
1. Click lock icon in browser address bar
2. Allow microphone permission
3. Refresh page

### Problem: "WebSocket connection failed"
**Solution**:
1. Verify backend is running: `http://localhost:8080`
2. Check browser console for errors
3. Ensure you're logged in with valid token

### Problem: "No transcription appearing"
**Solution**:
1. Check SarvamAI API key in backend `.env` file
2. Verify language selection matches your speech
3. Check backend console for errors
4. Ensure microphone is working (test in system settings)

### Problem: "CORS error"
**Solution**:
1. Use HTTP server instead of opening file directly
2. Check backend CORS settings in `settings.py`

## Next Steps

### For Testing:
1. Open **http://localhost:3000** in Chrome or Firefox
2. Login with your Django credentials
3. Test each feature systematically
4. Check browser console for any errors

### For Production:
1. Deploy backend to a server (Heroku, AWS, DigitalOcean)
2. Update frontend URLs to production backend
3. Deploy frontend to static hosting (Netlify, Vercel, GitHub Pages)
4. Use HTTPS and WSS (secure WebSocket)
5. Enable proper CORS settings
6. Set up environment variables securely

## Support Files

- **Frontend Documentation**: `frontend/README.md`
- **Backend API Docs**: `backend/LIVE_TRANSCRIPTION_API.md`
- **WebSocket Guide**: `backend/WEBSOCKET_CLIENT_GUIDE.md`

## Version

**v1.0 - 2025-11-06**

---

**Ready to test!** Open http://localhost:3000 and start transcribing in multiple Indian languages!
