"""
Transcription WebSocket Consumer
Handles real-time audio streaming and transcription using SarvamAI
"""

import json
import logging
import uuid
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

logger = logging.getLogger(__name__)


class TranscriptionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time speech-to-text transcription

    Protocol:
    1. Client connects with JWT token: ws://localhost:8080/ws/transcribe/?token=JWT_TOKEN
    2. Client sends config: {"type": "config", "language_code": "hi-IN"}
    3. Client streams audio: {"type": "audio", "data": "<base64_audio>"}
    4. Server returns transcription: {"type": "transcription", "text": "...", "is_final": false}
    5. Client sends end signal: {"type": "end"}
    6. Server returns final: {"type": "final", "text": "...", "transcription_id": 123}
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.session_id = None
        self.language_code = 'hi-IN'
        self.transcription_id = None
        self.audio_buffer = bytearray()
        self.full_transcription = ""

    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope.get('user', AnonymousUser())

        # Check if user is authenticated
        if isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            logger.warning("Unauthenticated WebSocket connection attempt")
            await self.close(code=4001)
            return

        # Generate unique session ID
        self.session_id = str(uuid.uuid4())

        logger.info(f"WebSocket connected - User: {self.user.username}, Session: {self.session_id}")

        # Accept the connection
        await self.accept()

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'session_id': self.session_id,
            'message': 'Connected to transcription service'
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        logger.info(f"WebSocket disconnected - User: {self.user.username if self.user else 'Unknown'}, Code: {close_code}")

        # Clean up resources if needed
        self.audio_buffer.clear()

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages"""
        try:
            if text_data:
                data = json.loads(text_data)
                message_type = data.get('type')

                if message_type == 'config':
                    await self.handle_config(data)
                elif message_type == 'audio':
                    await self.handle_audio(data)
                elif message_type == 'end':
                    await self.handle_end()
                else:
                    await self.send_error(f"Unknown message type: {message_type}")

            elif bytes_data:
                # Handle binary audio data directly
                await self.handle_audio_binary(bytes_data)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {str(e)}")
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_error(f"Error processing message: {str(e)}")

    async def handle_config(self, data):
        """Handle configuration message"""
        self.language_code = data.get('language_code', 'hi-IN')

        # Create transcription record in database
        self.transcription_id = await self.create_transcription()

        logger.info(f"Config set - Language: {self.language_code}, Transcription ID: {self.transcription_id}")

        await self.send(text_data=json.dumps({
            'type': 'config_confirmed',
            'language_code': self.language_code,
            'transcription_id': self.transcription_id
        }))

    async def handle_audio(self, data):
        """Handle audio data in base64 format"""
        try:
            # Decode base64 audio data
            audio_base64 = data.get('data', '')
            audio_bytes = base64.b64decode(audio_base64)

            # Add to buffer
            self.audio_buffer.extend(audio_bytes)

            logger.debug(f"Audio chunk received: {len(audio_bytes)} bytes, Buffer size: {len(self.audio_buffer)} bytes")

            # Process when buffer reaches threshold (e.g., 1 second of audio)
            # Assuming 16kHz, 16-bit, mono: 1 second = 32000 bytes
            if len(self.audio_buffer) >= 32000:
                await self.process_audio_buffer()

        except Exception as e:
            logger.error(f"Error handling audio: {str(e)}")
            await self.send_error(f"Error processing audio: {str(e)}")

    async def handle_audio_binary(self, audio_bytes):
        """Handle binary audio data"""
        try:
            # Add to buffer
            self.audio_buffer.extend(audio_bytes)

            logger.debug(f"Binary audio received: {len(audio_bytes)} bytes, Buffer size: {len(self.audio_buffer)} bytes")

            # Process when buffer reaches threshold
            if len(self.audio_buffer) >= 32000:
                await self.process_audio_buffer()

        except Exception as e:
            logger.error(f"Error handling binary audio: {str(e)}")
            await self.send_error(f"Error processing binary audio: {str(e)}")

    async def process_audio_buffer(self):
        """Process buffered audio data with SarvamAI"""
        try:
            audio_data = bytes(self.audio_buffer)
            self.audio_buffer.clear()

            # Call SarvamAI service
            result = await self.transcribe_audio(audio_data)

            if result['success']:
                transcription_text = result.get('transcription', '')

                # Append to full transcription
                self.full_transcription += transcription_text + " "

                # Update database
                await self.update_transcription(transcription_text, is_partial=True)

                # Send partial transcription to client
                await self.send(text_data=json.dumps({
                    'type': 'transcription',
                    'text': transcription_text,
                    'full_text': self.full_transcription.strip(),
                    'is_final': False
                }))

                logger.info(f"Partial transcription sent: {transcription_text[:50]}...")

            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Transcription failed: {error_msg}")
                await self.send_error(f"Transcription error: {error_msg}")

        except Exception as e:
            logger.error(f"Error processing audio buffer: {str(e)}")
            await self.send_error(f"Processing error: {str(e)}")

    async def handle_end(self):
        """Handle end of transcription"""
        try:
            # Process any remaining audio in buffer
            if len(self.audio_buffer) > 0:
                await self.process_audio_buffer()

            # Mark transcription as completed
            await self.mark_transcription_completed()

            # Send final transcription
            await self.send(text_data=json.dumps({
                'type': 'final',
                'text': self.full_transcription.strip(),
                'transcription_id': self.transcription_id,
                'language_code': self.language_code
            }))

            logger.info(f"Transcription completed - ID: {self.transcription_id}")

        except Exception as e:
            logger.error(f"Error handling end: {str(e)}")
            await self.send_error(f"Error finalizing transcription: {str(e)}")

    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

        # Mark transcription as failed if exists
        if self.transcription_id:
            await self.mark_transcription_failed(message)

    @database_sync_to_async
    def create_transcription(self):
        """Create transcription record in database"""
        from api.models import Transcription

        transcription = Transcription.objects.create(
            user=self.user,
            language_code=self.language_code,
            session_id=self.session_id,
            status='processing'
        )
        transcription.mark_as_processing()

        return transcription.id

    @database_sync_to_async
    def update_transcription(self, text, is_partial=True):
        """Update transcription in database"""
        from api.models import Transcription

        try:
            transcription = Transcription.objects.get(id=self.transcription_id)

            if is_partial:
                # Append to existing text
                current_text = transcription.transcription_text or ""
                transcription.transcription_text = (current_text + " " + text).strip()
            else:
                transcription.transcription_text = text

            transcription.save()

        except Transcription.DoesNotExist:
            logger.error(f"Transcription {self.transcription_id} not found")

    @database_sync_to_async
    def mark_transcription_completed(self):
        """Mark transcription as completed"""
        from api.models import Transcription

        try:
            transcription = Transcription.objects.get(id=self.transcription_id)
            transcription.mark_as_completed(self.full_transcription.strip())

        except Transcription.DoesNotExist:
            logger.error(f"Transcription {self.transcription_id} not found")

    @database_sync_to_async
    def mark_transcription_failed(self, error_message):
        """Mark transcription as failed"""
        from api.models import Transcription

        try:
            transcription = Transcription.objects.get(id=self.transcription_id)
            transcription.mark_as_failed(error_message)

        except Transcription.DoesNotExist:
            logger.error(f"Transcription {self.transcription_id} not found")

    @database_sync_to_async
    def transcribe_audio(self, audio_data):
        """Call SarvamAI service to transcribe audio"""
        from api.services.sarvam_service import get_sarvam_service

        service = get_sarvam_service()
        result = service.transcribe_audio_stream(
            audio_data=audio_data,
            language_code=self.language_code
        )

        return result
