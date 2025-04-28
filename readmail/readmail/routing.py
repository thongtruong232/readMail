from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/email_updates/$', consumers.EmailConsumer.as_asgi()),
] 