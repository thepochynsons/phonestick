from django.urls import re_path

from .consumers import JoystickConsumer

websocket_urlpatterns = [
    re_path(r"ws/joystick/(?P<room>[A-Za-z0-9_-]+)/$", JoystickConsumer.as_asgi()),
]
