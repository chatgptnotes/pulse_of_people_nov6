"""
JioTV Service Layer for Django Backend
Handles Tamil news channels streaming integration
"""

import requests
import logging
from typing import Dict, List, Optional
from django.core.cache import cache
from django.conf import settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class JioTVService:
    """
    Service class for JioTV integration in Django
    Provides methods to authenticate, fetch channels, and get stream URLs
    """

    # Tamil news channel IDs (as per JioTV)
    TAMIL_NEWS_CHANNELS = {
        '1561': 'Sun News',
        '1557': 'Puthiya Thalaimurai',
        '1559': 'Thanthi TV',
        '538': 'News 7 Tamil',
        '520': 'Captain News',
        '526': 'Kalaignar Seithigal',
        '1121': 'Raj News 24x7',
    }

    def __init__(self):
        self.base_url = getattr(settings, 'JIOTV_API_URL', 'http://localhost:8000')
        self.session = requests.Session()
        self.session.timeout = 10
        self.auth_token = self._get_cached_token()

        if self.auth_token:
            self._set_auth_header()

    def _get_cached_token(self) -> Optional[str]:
        """Retrieve cached authentication token"""
        return cache.get('jiotv_auth_token')

    def _cache_token(self, token: str, expiry_seconds: int = 82800):
        """Cache authentication token (default 23 hours)"""
        cache.set('jiotv_auth_token', token, expiry_seconds)
        self.auth_token = token
        self._set_auth_header()

    def _set_auth_header(self):
        """Set authorization header for requests"""
        if self.auth_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.auth_token}'
            })

    def check_service_health(self) -> Dict:
        """Check if JioTV-Proxy service is running"""
        try:
            response = self.session.get(
                f'{self.base_url}/health',
                timeout=5
            )
            return {
                'status': 'online' if response.status_code == 200 else 'offline',
                'status_code': response.status_code,
                'timestamp': datetime.now().isoformat()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"JioTV service health check failed: {e}")
            return {
                'status': 'offline',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def send_otp(self, mobile: str) -> Dict:
        """
        Send OTP to mobile number for authentication

        Args:
            mobile: Mobile number with country code (e.g., 91XXXXXXXXXX)

        Returns:
            Dict with success status and message
        """
        try:
            url = f'{self.base_url}/login/sendOTP'
            response = self.session.post(url, json={'mobile': mobile})

            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'OTP sent successfully',
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to send OTP',
                    'error': response.text
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send OTP: {e}")
            return {
                'success': False,
                'message': 'Network error while sending OTP',
                'error': str(e)
            }

    def verify_otp(self, mobile: str, otp: str) -> Dict:
        """
        Verify OTP and get authentication token

        Args:
            mobile: Mobile number with country code
            otp: OTP received via SMS

        Returns:
            Dict with success status and token
        """
        try:
            url = f'{self.base_url}/login/verifyOTP'
            response = self.session.post(url, json={
                'mobile': mobile,
                'otp': otp
            })

            if response.status_code == 200:
                data = response.json()
                token = data.get('token')

                if token:
                    self._cache_token(token)
                    logger.info(f"Successfully authenticated JioTV for mobile: {mobile}")
                    return {
                        'success': True,
                        'message': 'Authentication successful',
                        'token': token
                    }
                else:
                    return {
                        'success': False,
                        'message': 'No token received',
                        'data': data
                    }
            else:
                return {
                    'success': False,
                    'message': 'OTP verification failed',
                    'error': response.text
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to verify OTP: {e}")
            return {
                'success': False,
                'message': 'Network error during verification',
                'error': str(e)
            }

    def authenticate_with_password(self, mobile: str, password: str) -> Dict:
        """
        Authenticate using mobile and password

        Args:
            mobile: Mobile number with country code
            password: Account password

        Returns:
            Dict with success status and token
        """
        try:
            url = f'{self.base_url}/login'
            response = self.session.get(url, params={
                'username': mobile,
                'password': password
            })

            if response.status_code == 200:
                data = response.json()
                token = data.get('token')

                if token:
                    self._cache_token(token)
                    logger.info(f"Password authentication successful for: {mobile}")
                    return {
                        'success': True,
                        'message': 'Authentication successful',
                        'token': token
                    }
                else:
                    return {
                        'success': False,
                        'message': 'No token received',
                        'data': data
                    }
            else:
                return {
                    'success': False,
                    'message': 'Authentication failed',
                    'error': response.text
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"Password authentication failed: {e}")
            return {
                'success': False,
                'message': 'Network error during authentication',
                'error': str(e)
            }

    def get_all_channels(self) -> List[Dict]:
        """
        Fetch all available channels from JioTV

        Returns:
            List of channel dictionaries
        """
        cache_key = 'jiotv_all_channels'
        channels = cache.get(cache_key)

        if channels:
            logger.info("Returning cached channels list")
            return channels

        try:
            url = f'{self.base_url}/channels'
            response = self.session.get(url)

            if response.status_code == 200:
                channels = response.json()
                # Cache for 6 hours
                cache.set(cache_key, channels, 21600)
                logger.info(f"Fetched {len(channels)} channels from JioTV")
                return channels
            else:
                logger.error(f"Failed to fetch channels: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching channels: {e}")
            return []

    def get_tamil_news_channels(self) -> List[Dict]:
        """
        Get only Tamil news channels

        Returns:
            List of Tamil news channel dictionaries
        """
        cache_key = 'jiotv_tamil_news_channels'
        channels = cache.get(cache_key)

        if channels:
            logger.info("Returning cached Tamil news channels")
            return channels

        all_channels = self.get_all_channels()

        if not all_channels:
            return []

        # Filter Tamil news channels
        tamil_news = []
        for channel in all_channels:
            if self._is_tamil_news_channel(channel):
                tamil_news.append(channel)

        # Also filter by known channel IDs
        for channel in all_channels:
            channel_id = str(channel.get('id', ''))
            if channel_id in self.TAMIL_NEWS_CHANNELS:
                if channel not in tamil_news:
                    tamil_news.append(channel)

        # Cache for 6 hours
        cache.set(cache_key, tamil_news, 21600)
        logger.info(f"Found {len(tamil_news)} Tamil news channels")

        return tamil_news

    def _is_tamil_news_channel(self, channel: Dict) -> bool:
        """
        Check if a channel is a Tamil news channel

        Args:
            channel: Channel dictionary

        Returns:
            Boolean indicating if it's a Tamil news channel
        """
        name = channel.get('name', '').lower()
        category = channel.get('category', '').lower()
        language = channel.get('language', '').lower()

        is_tamil = 'tamil' in language or 'tamil' in name
        is_news = 'news' in name or 'news' in category or 'seithigal' in name

        return is_tamil and is_news

    def get_channel_by_id(self, channel_id: str) -> Optional[Dict]:
        """
        Get specific channel by ID

        Args:
            channel_id: Channel ID

        Returns:
            Channel dictionary or None
        """
        channels = self.get_all_channels()

        for channel in channels:
            if str(channel.get('id')) == str(channel_id):
                return channel

        return None

    def get_stream_url(self, channel_id: str, quality: str = 'auto') -> str:
        """
        Get streaming URL for a specific channel

        Args:
            channel_id: Channel ID
            quality: Stream quality (low/medium/high/auto)

        Returns:
            Streaming URL (m3u8)
        """
        valid_qualities = ['low', 'medium', 'high', 'auto']

        if quality not in valid_qualities:
            quality = 'auto'

        if quality == 'auto':
            return f'{self.base_url}/live/{channel_id}'
        else:
            return f'{self.base_url}/live/{quality}/{channel_id}'

    def get_m3u_playlist(self, tamil_only: bool = False) -> str:
        """
        Get M3U playlist for IPTV players

        Args:
            tamil_only: If True, return only Tamil news channels

        Returns:
            M3U playlist content
        """
        try:
            if tamil_only:
                channels = self.get_tamil_news_channels()
                return self._generate_m3u_playlist(channels)
            else:
                url = f'{self.base_url}/channels?type=m3u'
                response = self.session.get(url)

                if response.status_code == 200:
                    return response.text
                else:
                    logger.error(f"Failed to fetch M3U playlist: {response.status_code}")
                    return ""
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching M3U playlist: {e}")
            return ""

    def _generate_m3u_playlist(self, channels: List[Dict]) -> str:
        """
        Generate M3U playlist from channel list

        Args:
            channels: List of channel dictionaries

        Returns:
            M3U format string
        """
        m3u_content = "#EXTM3U\n"

        for channel in channels:
            channel_id = channel.get('id')
            channel_name = channel.get('name', 'Unknown')
            logo_url = channel.get('logoUrl', '')

            m3u_content += f'#EXTINF:-1 tvg-logo="{logo_url}",{channel_name}\n'
            m3u_content += f'{self.get_stream_url(channel_id, "high")}\n'

        return m3u_content

    def get_channel_epg(self, channel_id: str) -> Dict:
        """
        Get Electronic Program Guide (EPG) for a channel
        Note: This may not be available in all JioTV-Proxy versions

        Args:
            channel_id: Channel ID

        Returns:
            EPG data dictionary
        """
        try:
            url = f'{self.base_url}/epg/{channel_id}'
            response = self.session.get(url)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"EPG not available for channel {channel_id}")
                return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching EPG: {e}")
            return {}

    def clear_cache(self):
        """Clear all JioTV-related cache"""
        cache.delete('jiotv_auth_token')
        cache.delete('jiotv_all_channels')
        cache.delete('jiotv_tamil_news_channels')
        logger.info("JioTV cache cleared")

    def is_authenticated(self) -> bool:
        """Check if service is authenticated"""
        return bool(self.auth_token)

    def get_authentication_status(self) -> Dict:
        """Get detailed authentication status"""
        token = self._get_cached_token()

        return {
            'authenticated': bool(token),
            'token_exists': bool(token),
            'service_url': self.base_url,
            'timestamp': datetime.now().isoformat()
        }
