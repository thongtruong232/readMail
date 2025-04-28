import json
from channels.generic.websocket import AsyncWebsocketConsumer
from urllib.parse import parse_qs

class EmailConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            query_string = self.scope['query_string'].decode()
            query_params = parse_qs(query_string)
            self.client_id = query_params.get('client_id', [None])[0]

            if not self.client_id:
                await self.close()
                return

            self.group_name = f"client_{self.client_id}"

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, "group_name"):
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
            await self.close()
        except Exception as e:
            print(f"WebSocket disconnect error: {e}")

    async def email_update(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            print(f"WebSocket send error: {e}")
