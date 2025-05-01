# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Delivery

User = get_user_model()

class DeliveryTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.delivery_id = self.scope['url_route']['kwargs']['delivery_id']
        self.group_name = f'delivery_{self.delivery_id}'

        # Check if the user is authenticated
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        self.user = user

        # Check if user is the driver or customer of this delivery
        delivery = await self.get_delivery()
        if not delivery:
            await self.close()
            return

        self.delivery = delivery

        is_driver = delivery.driver and delivery.driver.user == user
        is_customer = delivery.order.customer == user

        if not (is_driver or is_customer):
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Only driver sends updates
        if self.delivery.driver and self.delivery.driver.user == self.user:
            lat = data.get("lat")
            lng = data.get("lng")

            if lat and lng:
                # Save to DB (optional)
                await self.update_driver_location(lat, lng)

                # Broadcast to the group (customer will receive)
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "send_location",
                        "lat": str(lat),
                        "lng": str(lng),
                        "delivery_id": self.delivery_id,
                    }
                )

    async def send_location(self, event):
        await self.send(text_data=json.dumps({
            "type": "location_update",
            "lat": event["lat"],
            "lng": event["lng"],
            "delivery_id": event["delivery_id"],
        }))

    @database_sync_to_async
    def get_delivery(self):
        try:
            return Delivery.objects.select_related('driver__user', 'order__customer').get(delivery_id=self.delivery_id)
        except Delivery.DoesNotExist:
            return None

    @database_sync_to_async
    def update_driver_location(self, lat, lng):
        self.delivery.driver_current_lat = lat
        self.delivery.driver_current_lng = lng
        self.delivery.save(update_fields=["driver_current_lat", "driver_current_lng", "last_updated"])
