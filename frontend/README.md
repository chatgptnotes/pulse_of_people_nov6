# Live Transcription Frontend

A standalone web application for real-time speech-to-text transcription using SarvamAI. Supports multiple Indian languages with live streaming audio transcription.

## Features

- **Real-time Transcription**: Live audio streaming with instant speech-to-text conversion
- **Multi-language Support**: 10 Indian languages including Hindi, English, Tamil, Telugu, and more
- **User Authentication**: Secure JWT-based authentication
- **Transcription History**: View, search, and filter past transcriptions
- **Export Functionality**: Download transcriptions as text files
- **Statistics Dashboard**: Track your usage and transcription metrics
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Prerequisites

- Modern web browser with:
  - WebSocket support
  - MediaRecorder API support (Chrome, Firefox, Edge)
  - Microphone access permission
- Backend API running on `http://localhost:8080`

## Quick Start

### 1. Ensure Backend is Running

Make sure the Django backend is running:

```bash
cd backend
source venv/bin/activate
python manage.py runserver 8080
```

The backend should be accessible at `http://localhost:8080`

### 2. Open the Frontend

Simply open `index.html` in your web browser:

```bash
# Option 1: Open directly
open frontend/index.html

# Option 2: Use a simple HTTP server (recommended)
cd frontend
python -m http.server 3000
```

Then navigate to `http://localhost:3000` in your browser.

### 3. Login

Use your Django credentials to log in:
- **Username**: Your Django username
- **Password**: Your Django password

If you don't have an account, create one using Django admin or the backend API.

## Usage Guide

### Recording a Transcription

1. **Select Language**: Choose your desired language from the dropdown (default: Hindi)
2. **Click "Start Recording"**: Allow microphone access when prompted
3. **Speak**: The live transcription will appear in real-time
4. **Click "Stop Recording"**: Processing will complete and save the transcription

### Viewing History

- All your transcriptions appear in the "History" section
- Use filters to narrow down results:
  - **Status**: Filter by pending, processing, completed, or failed
  - **Language**: Filter by specific language
  - **Search**: Search transcription text
- Click the eye icon to view full details
- Click the download icon to export as text file
- Click the delete icon to remove a transcription

### Understanding Statistics

The dashboard shows:
- **Total Transcriptions**: All transcriptions created
- **Completed**: Successfully processed transcriptions
- **Failed**: Transcriptions that encountered errors
- **Total Duration**: Combined audio duration in minutes

## File Structure

```
frontend/
├── index.html          # Main HTML file
├── css/
│   └── styles.css      # Stylesheet
├── js/
│   ├── app.js          # Main application logic
│   ├── auth.js         # Authentication module
│   ├── api.js          # REST API client
│   ├── websocket.js    # WebSocket client
│   ├── audio.js        # Audio recording module
│   └── ui.js           # UI updates and DOM manipulation
└── README.md           # This file
```

## Configuration

### Backend URL

By default, the app connects to `http://localhost:8080`. To change this:

1. Open `js/auth.js` and update:
```javascript
API_URL: 'http://your-backend-url/api'
```

2. Open `js/websocket.js` and update:
```javascript
const wsUrl = `ws://your-backend-url/ws/transcribe/?token=${token}`;
```

### Audio Settings

Audio recording settings can be modified in `js/audio.js`:

```javascript
audio: {
    channelCount: 1,      // Mono audio
    sampleRate: 16000,    // 16kHz sample rate
    echoCancellation: true,
    noiseSuppression: true
}
```

## Supported Languages

The application supports the following languages:

- Hindi (hi-IN)
- English - India (en-IN)
- Tamil (ta-IN)
- Telugu (te-IN)
- Bengali (bn-IN)
- Marathi (mr-IN)
- Gujarati (gu-IN)
- Kannada (kn-IN)
- Malayalam (ml-IN)
- Punjabi (pa-IN)

## Troubleshooting

### Microphone Access Denied

**Problem**: Browser blocks microphone access

**Solution**:
- Click the lock icon in the address bar
- Allow microphone permissions
- Refresh the page

### WebSocket Connection Failed

**Problem**: Cannot connect to backend

**Solution**:
- Ensure backend is running on port 8080
- Check browser console for specific error messages
- Verify your authentication token is valid

### No Transcription Appearing

**Problem**: Audio is being recorded but no text appears

**Solution**:
- Check your internet connection
- Verify the selected language is correct
- Ensure you're speaking clearly into the microphone
- Check backend logs for errors

### CORS Errors

**Problem**: Cross-origin request blocked

**Solution**:
- Use a local HTTP server instead of opening `index.html` directly
- Ensure backend CORS settings allow your frontend origin

### Authentication Errors

**Problem**: Login fails or token expires

**Solution**:
- Verify your username and password are correct
- Check if your account is active in Django admin
- Clear browser localStorage and try logging in again

## Browser Compatibility

### Fully Supported
- Chrome 60+
- Firefox 55+
- Edge 79+
- Opera 47+

### Partially Supported
- Safari 14+ (may have audio issues)

### Not Supported
- Internet Explorer (any version)
- Safari < 14

## Performance Tips

1. **Use Chrome or Firefox** for best audio recording performance
2. **Close unnecessary tabs** to reduce CPU usage
3. **Use a good quality microphone** for better transcription accuracy
4. **Speak clearly** and avoid background noise
5. **Stop recording** when not speaking to save resources

## Deployment

### Deploy to Static Hosting

Since this is a standalone HTML/JS app, you can deploy it to any static hosting service:

#### GitHub Pages

1. Push the `frontend` folder to a GitHub repository
2. Enable GitHub Pages in repository settings
3. Select the branch and folder
4. Access at `https://username.github.io/repo-name/`

#### Netlify

1. Drag and drop the `frontend` folder to Netlify
2. Or connect your Git repository
3. Deploy automatically

#### Vercel

```bash
cd frontend
vercel
```

### Update Backend URL

After deployment, update the backend URLs in:
- `js/auth.js` - Update `API_URL`
- `js/websocket.js` - Update WebSocket URL
- Ensure your backend allows the frontend origin in CORS settings

## Security Considerations

1. **HTTPS Required**: For production, use HTTPS for both frontend and backend
2. **Secure WebSocket**: Use `wss://` instead of `ws://` in production
3. **Token Storage**: Tokens are stored in localStorage (consider security implications)
4. **Microphone Privacy**: Always request permission and indicate when recording

## API Endpoints Used

### REST API
- `POST /api/auth/login/` - User authentication
- `POST /api/auth/refresh/` - Refresh access token
- `GET /api/transcriptions/` - List transcriptions
- `GET /api/transcriptions/{id}/` - Get transcription details
- `DELETE /api/transcriptions/{id}/` - Delete transcription
- `GET /api/transcriptions/stats/` - Get user statistics
- `GET /api/transcriptions/languages/` - Get supported languages
- `GET /api/transcriptions/{id}/export/` - Export transcription

### WebSocket
- `ws://localhost:8080/ws/transcribe/?token={JWT}` - Real-time transcription

## Development

### Local Testing

1. Start backend:
```bash
cd backend
python manage.py runserver 8080
```

2. Start frontend server:
```bash
cd frontend
python -m http.server 3000
```

3. Open browser to `http://localhost:3000`

### Debugging

Enable browser console to see:
- WebSocket connection status
- Audio recording events
- API request/response logs
- Error messages

## Version History

- **v1.0** - 2025-11-06
  - Initial release
  - Real-time transcription with WebSocket
  - Multi-language support
  - User authentication
  - Transcription history and statistics

## Support

For backend API documentation, see:
- `backend/LIVE_TRANSCRIPTION_API.md` - Complete API reference
- `backend/WEBSOCKET_CLIENT_GUIDE.md` - WebSocket integration guide

## License

This project is part of the PulseOfPeople Django application.

---

**v1.0 - 2025-11-06**
