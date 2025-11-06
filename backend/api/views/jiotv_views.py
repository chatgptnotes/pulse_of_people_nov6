"""
JioTV API Views for Tamil News Channels
Handles authentication, channel listing, and streaming
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import timedelta
import logging

from api.services.jiotv_service import JioTVService
from api.models import TVChannel, StreamSession, JioTVAuthentication

logger = logging.getLogger(__name__)


class JioTVHealthCheckView(APIView):
    """Check JioTV-Proxy service health"""
    permission_classes = [AllowAny]

    def get(self, request):
        service = JioTVService()
        health_status = service.check_service_health()

        return Response(health_status, status=status.HTTP_200_OK)


class JioTVAuthSendOTPView(APIView):
    """Send OTP for JioTV authentication"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        mobile = request.data.get('mobile')

        if not mobile:
            return Response({
                'success': False,
                'message': 'Mobile number is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        service = JioTVService()
        result = service.send_otp(mobile)

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class JioTVAuthVerifyOTPView(APIView):
    """Verify OTP and authenticate"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        mobile = request.data.get('mobile')
        otp = request.data.get('otp')

        if not mobile or not otp:
            return Response({
                'success': False,
                'message': 'Mobile number and OTP are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        service = JioTVService()
        result = service.verify_otp(mobile, otp)

        if result['success']:
            # Save authentication to database
            token_expires_at = timezone.now() + timedelta(hours=23)

            auth, created = JioTVAuthentication.objects.update_or_create(
                mobile_number=mobile,
                defaults={
                    'user': request.user,
                    'auth_token': result['token'],
                    'is_active': True,
                    'token_expires_at': token_expires_at,
                    'login_method': 'otp'
                }
            )

            return Response({
                'success': True,
                'message': 'Authentication successful',
                'expires_at': token_expires_at.isoformat()
            }, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class JioTVAuthPasswordView(APIView):
    """Authenticate with password"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        mobile = request.data.get('mobile')
        password = request.data.get('password')

        if not mobile or not password:
            return Response({
                'success': False,
                'message': 'Mobile number and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        service = JioTVService()
        result = service.authenticate_with_password(mobile, password)

        if result['success']:
            # Save authentication to database
            token_expires_at = timezone.now() + timedelta(hours=23)

            auth, created = JioTVAuthentication.objects.update_or_create(
                mobile_number=mobile,
                defaults={
                    'user': request.user,
                    'auth_token': result['token'],
                    'is_active': True,
                    'token_expires_at': token_expires_at,
                    'login_method': 'password'
                }
            )

            return Response({
                'success': True,
                'message': 'Authentication successful',
                'expires_at': token_expires_at.isoformat()
            }, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class JioTVAuthStatusView(APIView):
    """Get authentication status"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = JioTVService()
        auth_status = service.get_authentication_status()

        # Check database for user authentication
        user_auth = JioTVAuthentication.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if user_auth:
            auth_status['database_auth'] = {
                'mobile': user_auth.mobile_number,
                'expires_at': user_auth.token_expires_at.isoformat(),
                'is_expired': user_auth.is_token_expired(),
                'login_method': user_auth.login_method
            }

        return Response(auth_status, status=status.HTTP_200_OK)


class TamilNewsChannelsView(APIView):
    """Get list of Tamil news channels"""
    permission_classes = [AllowAny]

    def get(self, request):
        service = JioTVService()
        channels = service.get_tamil_news_channels()

        # Update database
        for channel_data in channels:
            channel_id = str(channel_data.get('id'))
            TVChannel.objects.update_or_create(
                channel_id=channel_id,
                defaults={
                    'name': channel_data.get('name', 'Unknown'),
                    'logo_url': channel_data.get('logoUrl', ''),
                    'language': 'tamil',
                    'category': 'news',
                    'is_hd': channel_data.get('isHD', False),
                    'is_active': True
                }
            )

        return Response({
            'count': len(channels),
            'channels': channels,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)


class AllChannelsView(APIView):
    """Get all available channels"""
    permission_classes = [AllowAny]

    def get(self, request):
        service = JioTVService()
        channels = service.get_all_channels()

        return Response({
            'count': len(channels),
            'channels': channels,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)


class ChannelDetailView(APIView):
    """Get specific channel details"""
    permission_classes = [AllowAny]

    def get(self, request, channel_id):
        service = JioTVService()
        channel = service.get_channel_by_id(channel_id)

        if not channel:
            return Response({
                'success': False,
                'message': f'Channel {channel_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get stream URLs
        stream_urls = {
            'low': service.get_stream_url(channel_id, 'low'),
            'medium': service.get_stream_url(channel_id, 'medium'),
            'high': service.get_stream_url(channel_id, 'high'),
            'auto': service.get_stream_url(channel_id, 'auto')
        }

        channel['stream_urls'] = stream_urls

        # Update view count in database
        try:
            db_channel = TVChannel.objects.get(channel_id=channel_id)
            db_channel.increment_view_count()
        except TVChannel.DoesNotExist:
            pass

        return Response(channel, status=status.HTTP_200_OK)


class ChannelStreamView(APIView):
    """Get stream URL for a channel"""
    permission_classes = [IsAuthenticated]

    def get(self, request, channel_id):
        quality = request.query_params.get('quality', 'auto')
        service = JioTVService()

        stream_url = service.get_stream_url(channel_id, quality)

        # Create stream session
        try:
            db_channel, created = TVChannel.objects.get_or_create(
                channel_id=channel_id,
                defaults={'name': f'Channel {channel_id}'}
            )

            session = StreamSession.objects.create(
                user=request.user,
                channel=db_channel,
                quality=quality,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )

            logger.info(f"Stream session created: {session.id} for user {request.user.username}")
        except Exception as e:
            logger.error(f"Failed to create stream session: {e}")

        return Response({
            'channel_id': channel_id,
            'stream_url': stream_url,
            'quality': quality,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class EndStreamSessionView(APIView):
    """End a stream session"""
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        try:
            session = StreamSession.objects.get(
                id=session_id,
                user=request.user
            )
            session.end_session()

            return Response({
                'success': True,
                'message': 'Stream session ended',
                'duration_seconds': session.duration_seconds
            }, status=status.HTTP_200_OK)
        except StreamSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Stream session not found'
            }, status=status.HTTP_404_NOT_FOUND)


class M3UPlaylistView(APIView):
    """Get M3U playlist for IPTV players"""
    permission_classes = [AllowAny]

    def get(self, request):
        tamil_only = request.query_params.get('tamil_only', 'false').lower() == 'true'

        service = JioTVService()
        playlist = service.get_m3u_playlist(tamil_only=tamil_only)

        response = HttpResponse(playlist, content_type='application/x-mpegurl')
        response['Content-Disposition'] = 'attachment; filename="jiotv_tamil_news.m3u"'

        return response


class ChannelEPGView(APIView):
    """Get Electronic Program Guide for a channel"""
    permission_classes = [AllowAny]

    def get(self, request, channel_id):
        service = JioTVService()
        epg = service.get_channel_epg(channel_id)

        if epg:
            return Response(epg, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'EPG not available for this channel'
            }, status=status.HTTP_404_NOT_FOUND)


class UserStreamHistoryView(APIView):
    """Get user's streaming history"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = StreamSession.objects.filter(
            user=request.user
        ).select_related('channel')[:50]

        history = []
        for session in sessions:
            history.append({
                'id': session.id,
                'channel': {
                    'id': session.channel.channel_id,
                    'name': session.channel.name
                },
                'quality': session.quality,
                'status': session.status,
                'started_at': session.started_at.isoformat(),
                'ended_at': session.ended_at.isoformat() if session.ended_at else None,
                'duration_seconds': session.duration_seconds
            })

        return Response({
            'count': len(history),
            'history': history
        }, status=status.HTTP_200_OK)


class ChannelStatisticsView(APIView):
    """Get channel statistics"""
    permission_classes = [AllowAny]

    def get(self, request):
        # Most viewed channels
        most_viewed = TVChannel.objects.filter(
            is_active=True,
            language='tamil',
            category='news'
        ).order_by('-view_count')[:10]

        # Recently viewed
        recently_viewed = TVChannel.objects.filter(
            is_active=True,
            language='tamil',
            category='news',
            last_viewed_at__isnull=False
        ).order_by('-last_viewed_at')[:10]

        stats = {
            'most_viewed': [
                {
                    'channel_id': ch.channel_id,
                    'name': ch.name,
                    'view_count': ch.view_count,
                    'logo_url': ch.logo_url
                } for ch in most_viewed
            ],
            'recently_viewed': [
                {
                    'channel_id': ch.channel_id,
                    'name': ch.name,
                    'last_viewed_at': ch.last_viewed_at.isoformat() if ch.last_viewed_at else None,
                    'logo_url': ch.logo_url
                } for ch in recently_viewed
            ],
            'total_channels': TVChannel.objects.filter(language='tamil', category='news').count(),
            'total_sessions': StreamSession.objects.filter(channel__language='tamil').count()
        }

        return Response(stats, status=status.HTTP_200_OK)


class ClearCacheView(APIView):
    """Clear JioTV cache"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Only allow superusers to clear cache
        if not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)

        service = JioTVService()
        service.clear_cache()

        return Response({
            'success': True,
            'message': 'Cache cleared successfully'
        }, status=status.HTTP_200_OK)
