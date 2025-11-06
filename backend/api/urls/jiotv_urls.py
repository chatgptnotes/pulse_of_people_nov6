"""
URL Configuration for JioTV API endpoints
"""

from django.urls import path
from api.views.jiotv_views import (
    JioTVHealthCheckView,
    JioTVAuthSendOTPView,
    JioTVAuthVerifyOTPView,
    JioTVAuthPasswordView,
    JioTVAuthStatusView,
    TamilNewsChannelsView,
    AllChannelsView,
    ChannelDetailView,
    ChannelStreamView,
    EndStreamSessionView,
    M3UPlaylistView,
    ChannelEPGView,
    UserStreamHistoryView,
    ChannelStatisticsView,
    ClearCacheView,
)

app_name = 'jiotv'

urlpatterns = [
    # Health check
    path('health/', JioTVHealthCheckView.as_view(), name='health-check'),

    # Authentication
    path('auth/send-otp/', JioTVAuthSendOTPView.as_view(), name='auth-send-otp'),
    path('auth/verify-otp/', JioTVAuthVerifyOTPView.as_view(), name='auth-verify-otp'),
    path('auth/password/', JioTVAuthPasswordView.as_view(), name='auth-password'),
    path('auth/status/', JioTVAuthStatusView.as_view(), name='auth-status'),

    # Channels
    path('channels/tamil-news/', TamilNewsChannelsView.as_view(), name='tamil-news-channels'),
    path('channels/all/', AllChannelsView.as_view(), name='all-channels'),
    path('channels/<str:channel_id>/', ChannelDetailView.as_view(), name='channel-detail'),

    # Streaming
    path('stream/<str:channel_id>/', ChannelStreamView.as_view(), name='channel-stream'),
    path('stream/session/<int:session_id>/end/', EndStreamSessionView.as_view(), name='end-stream-session'),

    # Playlists
    path('playlist/', M3UPlaylistView.as_view(), name='m3u-playlist'),

    # EPG (Electronic Program Guide)
    path('epg/<str:channel_id>/', ChannelEPGView.as_view(), name='channel-epg'),

    # User history
    path('history/', UserStreamHistoryView.as_view(), name='user-history'),

    # Statistics
    path('statistics/', ChannelStatisticsView.as_view(), name='statistics'),

    # Admin
    path('admin/clear-cache/', ClearCacheView.as_view(), name='clear-cache'),
]
