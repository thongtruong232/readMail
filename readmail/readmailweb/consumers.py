import json
from channels.generic.websocket import AsyncWebsocketConsumer
from urllib.parse import parse_qs

class EmailConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print('==> [EmailConsumer] connect called')
        query_string = self.scope['query_string'].decode()
        query_params = parse_qs(query_string)
        self.client_id = query_params.get('client_id', [None])[0]
        print(f"==> [EmailConsumer] client_id: {self.client_id}")
        if not self.client_id:
            print('==> [EmailConsumer] No client_id, closing connection')
            await self.close()
            return
        self.group_name = f"client_{self.client_id}"
        print(f"==> [EmailConsumer] Adding to group: {self.group_name}")
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        print('==> [EmailConsumer] Connection accepted')

    async def disconnect(self, close_code):
        print(f"==> [EmailConsumer] disconnect called, close_code: {close_code}")
        try:
            if hasattr(self, "group_name"):
                print(f"==> [EmailConsumer] Discarding from group: {self.group_name}")
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
            await self.close()
            print('==> [EmailConsumer] Connection closed')
        except Exception as e:
            print(f"Error during WebSocket disconnect: {e}")

    async def email_update(self, event):
        print(f"==> [EmailConsumer] email_update called, event: {event}")
        await self.send(text_data=json.dumps(event))
