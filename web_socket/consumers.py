from channels.generic.websocket import AsyncWebsocketConsumer
import json

class RobotControlConsumers(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def sent_count(self, event):
        count = event['count']

        await self.send(text_data=json.dumps({
            'count': count
        }))

