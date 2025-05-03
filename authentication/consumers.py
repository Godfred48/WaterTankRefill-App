import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Delivery

class DeliveryTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.delivery_id = self.scope['url_route']['kwargs']['delivery_id']
        self.room_group_name = f'delivery_{self.delivery_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        lat = data['lat']
        lng = data['lng']
        role = data['role']

        # Broadcast location to the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'location_update',
                'role': role,
                'lat': lat,
                'lng': lng
            }
        )

        # Optionally update DB (skip if you want minimal writes)
        delivery = await self.get_delivery()
        if role == "driver":
            delivery.driver_current_lat = lat
            delivery.driver_current_lng = lng
        elif role == "customer":
            delivery.customer_lat = lat
            delivery.customer_lng = lng
        await database_sync_to_async(delivery.save)()

    async def location_update(self, event):
        await self.send(text_data=json.dumps({
            'role': event['role'],
            'lat': event['lat'],
            'lng': event['lng']
        }))

    @database_sync_to_async
    def get_delivery(self):
        return Delivery.objects.get(delivery_id=self.delivery_id)
