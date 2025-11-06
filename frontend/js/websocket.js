/**
 * WebSocket Module
 * Handles WebSocket connection for live transcription
 */

const WebSocketClient = {
    ws: null,
    isConnected: false,
    transcriptionId: null,
    sessionId: null,
    fullTranscription: '',
    reconnectAttempts: 0,
    maxReconnectAttempts: 3,
    onTranscription: null,
    onFinal: null,
    onError: null,
    onStatusChange: null,

    /**
     * Connect to WebSocket server
     */
    connect(languageCode) {
        return new Promise((resolve, reject) => {
            const token = Auth.getToken();
            if (!token) {
                reject(new Error('No authentication token'));
                return;
            }

            const wsUrl = `ws://localhost:8080/ws/transcribe/?token=${token}`;

            try {
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    this.fullTranscription = '';

                    if (this.onStatusChange) {
                        this.onStatusChange('connected');
                    }

                    // Send config immediately after connection
                    this.sendConfig(languageCode);
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(event.data);
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    if (this.onError) {
                        this.onError('Connection error');
                    }
                };

                this.ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    this.isConnected = false;

                    if (this.onStatusChange) {
                        this.onStatusChange('disconnected');
                    }

                    // Auto-reconnect logic
                    if (this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.reconnectAttempts++;
                        setTimeout(() => {
                            this.connect(languageCode);
                        }, 2000 * this.reconnectAttempts);
                    }
                };

            } catch (error) {
                reject(error);
            }
        });
    },

    /**
     * Handle incoming WebSocket messages
     */
    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            console.log('Received:', message);

            switch (message.type) {
                case 'connected':
                    this.sessionId = message.session_id;
                    console.log('Session ID:', this.sessionId);
                    break;

                case 'config_confirmed':
                    this.transcriptionId = message.transcription_id;
                    console.log('Transcription ID:', this.transcriptionId);
                    break;

                case 'transcription':
                    this.fullTranscription = message.full_text;
                    if (this.onTranscription) {
                        this.onTranscription(message.text, message.full_text);
                    }
                    break;

                case 'final':
                    this.fullTranscription = message.text;
                    if (this.onFinal) {
                        this.onFinal(message.text, message.transcription_id);
                    }
                    break;

                case 'error':
                    if (this.onError) {
                        this.onError(message.message);
                    }
                    break;

                default:
                    console.log('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    },

    /**
     * Send configuration to server
     */
    sendConfig(languageCode) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected');
            return;
        }

        const config = {
            type: 'config',
            language_code: languageCode
        };

        this.ws.send(JSON.stringify(config));
        console.log('Sent config:', config);
    },

    /**
     * Send audio data
     */
    sendAudio(audioData) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected');
            return;
        }

        // Convert audio data to base64
        const reader = new FileReader();
        reader.onload = () => {
            const arrayBuffer = reader.result;
            const bytes = new Uint8Array(arrayBuffer);
            const base64Audio = btoa(String.fromCharCode.apply(null, bytes));

            const message = {
                type: 'audio',
                data: base64Audio
            };

            this.ws.send(JSON.stringify(message));
        };
        reader.readAsArrayBuffer(audioData);
    },

    /**
     * Send end signal
     */
    sendEnd() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected');
            return;
        }

        const message = {
            type: 'end'
        };

        this.ws.send(JSON.stringify(message));
        console.log('Sent end signal');
    },

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
            this.isConnected = false;
        }
    },

    /**
     * Set callback for transcription updates
     */
    setOnTranscription(callback) {
        this.onTranscription = callback;
    },

    /**
     * Set callback for final transcription
     */
    setOnFinal(callback) {
        this.onFinal = callback;
    },

    /**
     * Set callback for errors
     */
    setOnError(callback) {
        this.onError = callback;
    },

    /**
     * Set callback for status changes
     */
    setOnStatusChange(callback) {
        this.onStatusChange = callback;
    }
};
