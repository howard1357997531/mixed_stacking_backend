from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json

class RobotControlConsumers(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(
            'count_room',
            self.channel_name
        )
        print('socket connect')

    async def disconnect(self, close_code):
        print('disconnect')
        await self.channel_layer.group_discard('count_room', self.channel_name)

    async def send_count(self, event):
        count = event['count']

        await self.send(text_data=json.dumps({
            'count': count
        }))

    async def robot_count_change(self, event):
        await self.send_json({
            'count': event['count']
        })
    
    async def robot_mode_change(self, event):
        await self.send_json({
            'mode': event['mode']
        })
    



