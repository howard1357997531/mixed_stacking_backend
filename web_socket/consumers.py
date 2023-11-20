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

    async def object_count_change(self, event):
        await self.send_json({
            'count': event['count']
        })

    async def object_name_change(self, event):
        await self.send_json({
            'name': event['name'],
            'nextName': event['nextName'],
        })
    
    async def robot_mode_change(self, event):
        await self.send_json({
            'mode': event['mode']
        })

    async def visual_result_change(self, event):
        await self.send_json({
            'visual_result': event['visual_result'],
            'visual_count': event['visual_count'],
        })
    



