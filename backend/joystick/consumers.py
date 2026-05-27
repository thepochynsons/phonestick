import json
import time

from channels.generic.websocket import AsyncWebsocketConsumer


class JoystickConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room = self.scope["url_route"]["kwargs"]["room"]
        self.group_name = "joystick_%s" % self.room

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "joystick.event",
                "payload": {
                    "type": "peer-joined",
                    "sender": self.channel_name,
                    "timestamp": time.time(),
                },
            },
        )

    async def disconnect(self, _close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "joystick.event",
                "payload": {
                    "type": "peer-left",
                    "sender": self.channel_name,
                    "timestamp": time.time(),
                },
            },
        )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            payload = json.loads(text_data)
        except ValueError:
            return

        payload["sender"] = self.channel_name
        payload["timestamp"] = time.time()
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "joystick.event",
                "payload": payload,
            },
        )

    async def joystick_event(self, event):
        if event["payload"].get("sender") == self.channel_name:
            return

        await self.send(text_data=json.dumps(event["payload"]))
