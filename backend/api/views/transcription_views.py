"""
Transcription API Views
REST API endpoints for transcription management
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum
from api.models import Transcription
from api.serializers import TranscriptionSerializer, TranscriptionListSerializer
from api.services.sarvam_service import get_sarvam_service


class TranscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing transcriptions

    list:
    Get list of user's transcriptions

    retrieve:
    Get detailed transcription

    destroy:
    Delete a transcription

    languages:
    Get list of supported languages

    stats:
    Get transcription statistics for current user
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TranscriptionSerializer

    def get_queryset(self):
        """Get transcriptions for current user only"""
        user = self.request.user
        queryset = Transcription.objects.filter(user=user)

        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filter by language
        language_param = self.request.query_params.get('language', None)
        if language_param:
            queryset = queryset.filter(language_code=language_param)

        # Search in transcription text
        search_param = self.request.query_params.get('search', None)
        if search_param:
            queryset = queryset.filter(
                Q(transcription_text__icontains=search_param)
            )

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return TranscriptionListSerializer
        return TranscriptionSerializer

    def create(self, request, *args, **kwargs):
        """
        Creating transcriptions via REST API is disabled.
        Use WebSocket endpoint for real-time transcription.
        """
        return Response(
            {
                'error': 'Use WebSocket endpoint for transcription',
                'websocket_url': 'ws://localhost:8080/ws/transcribe/?token=YOUR_JWT_TOKEN',
                'instructions': 'Connect to WebSocket endpoint with JWT token to start transcription'
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def update(self, request, *args, **kwargs):
        """Disable update - transcriptions are read-only"""
        return Response(
            {'error': 'Transcriptions cannot be updated'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def partial_update(self, request, *args, **kwargs):
        """Disable partial update - transcriptions are read-only"""
        return Response(
            {'error': 'Transcriptions cannot be updated'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=False, methods=['get'])
    def languages(self, request):
        """Get list of supported languages"""
        service = get_sarvam_service()
        languages = service.get_supported_languages()

        return Response({
            'languages': languages,
            'default': 'hi-IN'
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get transcription statistics for current user"""
        user = request.user
        queryset = Transcription.objects.filter(user=user)

        stats = {
            'total_transcriptions': queryset.count(),
            'completed': queryset.filter(status='completed').count(),
            'processing': queryset.filter(status='processing').count(),
            'failed': queryset.filter(status='failed').count(),
            'by_language': {},
            'total_duration': 0
        }

        # Count by language
        for lang_code, lang_name in Transcription.LANGUAGE_CHOICES:
            count = queryset.filter(language_code=lang_code).count()
            if count > 0:
                stats['by_language'][lang_code] = {
                    'name': lang_name,
                    'count': count
                }

        # Calculate total audio duration
        total_duration = queryset.filter(
            audio_duration__isnull=False
        ).aggregate(
            total=Sum('audio_duration')
        )
        stats['total_duration'] = total_duration.get('total', 0) or 0

        return Response(stats)

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Export transcription as plain text"""
        transcription = self.get_object()

        response = Response(
            transcription.transcription_text,
            content_type='text/plain'
        )
        response['Content-Disposition'] = f'attachment; filename="transcription_{pk}.txt"'

        return response

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload audio file for transcription"""
        from django.core.files.uploadedfile import UploadedFile
        import tempfile
        import os
        from datetime import datetime

        # Get uploaded file
        audio_file = request.FILES.get('audio_file')
        if not audio_file:
            return Response(
                {'error': 'No audio file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get language code (default to Hindi)
        language_code = request.data.get('language_code', 'hi-IN')

        # Validate file size (max 25MB)
        if audio_file.size > 25 * 1024 * 1024:
            return Response(
                {'error': 'File size exceeds 25MB limit'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create transcription record
        transcription = Transcription.objects.create(
            user=request.user,
            language_code=language_code,
            status='processing',
            audio_metadata={
                'filename': audio_file.name,
                'size': audio_file.size,
                'content_type': audio_file.content_type
            },
            started_at=datetime.now()
        )

        try:
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as tmp_file:
                for chunk in audio_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            # Read file content
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()

            # Process with SarvamAI
            sarvam_service = get_sarvam_service()
            result = sarvam_service.transcribe_audio_stream(
                audio_data=audio_data,
                language_code=language_code
            )

            # Clean up temp file
            os.unlink(tmp_path)

            if result['success']:
                # Update transcription
                transcription.transcription_text = result['transcription']
                transcription.status = 'completed'
                transcription.completed_at = datetime.now()
                transcription.confidence_score = result.get('confidence', 0.0)

                # Calculate processing time
                if transcription.started_at:
                    processing_time = (datetime.now() - transcription.started_at).total_seconds()
                    transcription.audio_metadata['processing_time'] = processing_time

                transcription.save()

                # Serialize and return
                serializer = TranscriptionSerializer(transcription)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                # Update with error
                transcription.status = 'failed'
                transcription.error_message = result.get('error', 'Transcription failed')
                transcription.completed_at = datetime.now()
                transcription.save()

                return Response(
                    {'error': result.get('error', 'Transcription failed')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            # Clean up temp file if it exists
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)

            # Update transcription with error
            transcription.status = 'failed'
            transcription.error_message = str(e)
            transcription.completed_at = datetime.now()
            transcription.save()

            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
