/**
 * Audio Module
 * Handles microphone recording and audio streaming
 */

const AudioRecorder = {
    mediaRecorder: null,
    audioStream: null,
    isRecording: false,
    chunks: [],

    /**
     * Initialize and start recording
     */
    async startRecording(onDataAvailable) {
        try {
            // Request microphone access
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,  // Mono
                    sampleRate: 16000, // 16kHz
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: this.getSupportedMimeType()
            });

            // Handle data available event
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.chunks.push(event.data);
                    if (onDataAvailable) {
                        onDataAvailable(event.data);
                    }
                }
            };

            // Start recording with 1-second timeslice
            this.mediaRecorder.start(1000);
            this.isRecording = true;

            console.log('Recording started');
            return true;
        } catch (error) {
            console.error('Failed to start recording:', error);

            // User-friendly error messages
            if (error.name === 'NotAllowedError') {
                throw new Error('Microphone access denied. Please allow microphone access.');
            } else if (error.name === 'NotFoundError') {
                throw new Error('No microphone found. Please connect a microphone.');
            } else {
                throw new Error('Failed to access microphone: ' + error.message);
            }
        }
    },

    /**
     * Stop recording
     */
    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
            this.isRecording = false;
        }

        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }

        console.log('Recording stopped');
    },

    /**
     * Get supported MIME type
     */
    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/mp4',
            'audio/wav'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                console.log('Using MIME type:', type);
                return type;
            }
        }

        return ''; // Use default
    },

    /**
     * Check if recording is supported
     */
    isSupported() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
    },

    /**
     * Get all recorded chunks
     */
    getChunks() {
        return this.chunks;
    },

    /**
     * Clear recorded chunks
     */
    clearChunks() {
        this.chunks = [];
    },

    /**
     * Get combined audio blob
     */
    getAudioBlob() {
        return new Blob(this.chunks, { type: this.getSupportedMimeType() });
    }
};
