import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

class LiveLocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            self.user = self.scope["user"]
            self.group_name = "live_tracking"

            # Add user to tracking group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if latitude is not None and longitude is not None:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "send_location",
                    "user_id": self.user.id,
                    "full_name": await self.get_full_name(),
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )

    async def send_location(self, event):
        # Don't send your own location back to yourself
        if event["user_id"] != self.user.id:
            await self.send(text_data=json.dumps({
                "full_name": event["full_name"],
                "latitude": event["latitude"],
                "longitude": event["longitude"],
            }))

    @database_sync_to_async
    def get_full_name(self):
        return self.user.full_name
