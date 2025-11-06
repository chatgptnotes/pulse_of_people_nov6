"""
WebSocket URL Routing Configuration
Defines WebSocket endpoints for Django Channels
"""

from django.urls import re_path
from api.consumers import TranscriptionConsumer

websocket_urlpatterns = [
    re_path(r'ws/transcribe/$', TranscriptionConsumer.as_asgi()),
]
