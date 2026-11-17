from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Per-user notification channel."""

    async def connect(self):
        if self.scope['user'].is_anonymous:
            await self.close()
            return
        self.group_name = f'notifications_{self.scope["user"].id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notify(self, event):
        await self.send_json(event['data'])


class DonationFeedConsumer(AsyncJsonWebsocketConsumer):
    """Live donation feed — broadcasts new donations to all connected users."""

    async def connect(self):
        self.group_name = 'donation_feed'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def new_donation(self, event):
        await self.send_json(event['data'])


class TaskTrackingConsumer(AsyncJsonWebsocketConsumer):
    """Per-task real-time status updates."""

    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.group_name = f'task_{self.task_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def task_update(self, event):
        await self.send_json(event['data'])
