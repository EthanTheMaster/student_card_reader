import asyncio
import websockets
import json

class Backend:
    def __init__(self, card_reader_fn):
        start_server = websockets.serve(self.hello, "127.0.0.1", 8765)
        self.has_connection = False
        self.card_reader_fn = card_reader_fn

        print("Running Server on: {}:{}".format("127.0.0.1", "8765"))
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def hello(self, websocket, path):
        if not(self.has_connection):
            self.has_connection = True
            print("Client Connected...")
            while True:
                client_msg = await websocket.recv()
                if client_msg == "Ready":
                    student_name, student_id = await self.card_reader_fn()

                    await websocket.send(json.dumps({"name": student_name, "id": student_id}))
        exit()


