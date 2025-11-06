"""
SarvamAI Speech-to-Text Service
Handles integration with SarvamAI API for real-time transcription
"""

import logging
import requests
import io
import wave
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class SarvamAIService:
    """Service class for SarvamAI speech-to-text operations"""

    def __init__(self):
        """Initialize SarvamAI client"""
        self.api_key = settings.SARVAM_AI_API_KEY
        self.model = settings.SARVAM_AI_MODEL
        self.base_url = "https://api.sarvam.ai"

        if not self.api_key:
            logger.warning("SARVAM_AI_API_KEY not configured in settings")
        else:
            logger.info("SarvamAI service initialized successfully")

    def is_available(self) -> bool:
        """Check if SarvamAI service is available"""
        return bool(self.api_key)

    def convert_to_wav(self, audio_data: bytes) -> io.BytesIO:
        """
        Convert audio data to WAV format (16kHz, mono, 16-bit PCM)

        Args:
            audio_data: Raw audio bytes

        Returns:
            BytesIO object containing WAV data
        """
        try:
            # If already WAV format, return as is
            if audio_data[:4] == b'RIFF':
                return io.BytesIO(audio_data)

            # For WebM or other formats, create a simple WAV with the data
            # This is a simplified approach - ideally use pydub for conversion
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)  # 16kHz
                wav_file.writeframes(audio_data)

            wav_buffer.seek(0)
            return wav_buffer

        except Exception as e:
            logger.warning(f"Audio conversion failed, sending original: {e}")
            return io.BytesIO(audio_data)

    def transcribe_audio(
        self,
        audio_file,
        language_code: str = "",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using SarvamAI

        Args:
            audio_file: Audio file object or path
            language_code: Language code (e.g., 'hi-IN', 'ta-IN')
            model: Optional model override

        Returns:
            Dict containing transcription results
        """
        if not self.is_available():
            raise Exception("SarvamAI service is not available. Check API key configuration.")

        try:
            model_to_use = model or self.model

            logger.info(f"Starting transcription with language: {language_code}, model: {model_to_use}")

            headers = {
                'api-subscription-key': self.api_key
            }

            files = {
                'file': audio_file
            }

            data = {
                'language_code': language_code or 'unknown',
                'model': model_to_use
            }

            response = requests.post(
                f"{self.base_url}/speech-to-text",
                headers=headers,
                files=files,
                data=data
            )

            response.raise_for_status()
            result = response.json()

            logger.info("Transcription completed successfully")

            return {
                'success': True,
                'transcription': result.get('transcript', ''),
                'language_code': language_code,
                'model': model_to_use,
                'raw_response': result
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Transcription API request failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'language_code': language_code,
                'model': model_to_use
            }
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'language_code': language_code,
                'model': model_to_use
            }

    def transcribe_audio_stream(
        self,
        audio_data: bytes,
        language_code: str = "",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe streaming audio data

        Args:
            audio_data: Audio bytes
            language_code: Language code
            model: Optional model override

        Returns:
            Dict containing transcription results
        """
        if not self.is_available():
            raise Exception("SarvamAI service is not available. Check API key configuration.")

        try:
            # Convert audio to WAV format
            wav_buffer = self.convert_to_wav(audio_data)

            model_to_use = model or self.model

            logger.info(f"Starting stream transcription, original size: {len(audio_data)} bytes")

            headers = {
                'api-subscription-key': self.api_key
            }

            files = {
                'file': ('audio.wav', wav_buffer, 'audio/wav')
            }

            data = {
                'language_code': language_code or 'unknown',
                'model': model_to_use
            }

            response = requests.post(
                f"{self.base_url}/speech-to-text",
                headers=headers,
                files=files,
                data=data
            )

            response.raise_for_status()
            result = response.json()

            logger.info("Stream transcription completed")

            return {
                'success': True,
                'transcription': result.get('transcript', ''),
                'language_code': language_code,
                'model': model_to_use,
                'audio_size': len(audio_data)
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Stream transcription API request failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'language_code': language_code,
                'model': model_to_use
            }
        except Exception as e:
            logger.error(f"Stream transcription failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'language_code': language_code,
                'model': model_to_use
            }

    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return [
            {'code': 'hi-IN', 'name': 'Hindi'},
            {'code': 'en-IN', 'name': 'English (India)'},
            {'code': 'ta-IN', 'name': 'Tamil'},
            {'code': 'te-IN', 'name': 'Telugu'},
            {'code': 'kn-IN', 'name': 'Kannada'},
            {'code': 'ml-IN', 'name': 'Malayalam'},
            {'code': 'mr-IN', 'name': 'Marathi'},
            {'code': 'bn-IN', 'name': 'Bengali'},
            {'code': 'gu-IN', 'name': 'Gujarati'},
            {'code': 'pa-IN', 'name': 'Punjabi'},
        ]


# Singleton instance
_sarvam_service = None


def get_sarvam_service() -> SarvamAIService:
    """Get singleton SarvamAI service instance"""
    global _sarvam_service
    # Always recreate in development to pick up code changes
    from django.conf import settings
    if settings.DEBUG:
        _sarvam_service = SarvamAIService()
    elif _sarvam_service is None:
        _sarvam_service = SarvamAIService()
    return _sarvam_service
