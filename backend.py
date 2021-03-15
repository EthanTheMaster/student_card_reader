import asyncio
import websockets
import json
import pathlib
import ssl

server_ip = "127.0.0.1"

class Backend:
    def __init__(self, card_reader_fn):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        public_pem = pathlib.Path(__file__).with_name("public.pem")
        private_pem = pathlib.Path(__file__).with_name("private.pem")
        ssl_context.load_cert_chain(certfile=public_pem, keyfile=private_pem, password=None)

        start_server = websockets.serve(self.hello, server_ip, 8765, ssl=ssl_context)
        self.has_connection = False
        self.card_reader_fn = card_reader_fn

        print("Running Server on: {}:{}".format(server_ip, "8765"))

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


