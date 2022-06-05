import asyncio
import json
import sys

class Client:

    def __init__(self, address, port):
        self.address = address
        self.port = port

    def send(self, request):
        async def communicate():
            reader, writer = await asyncio.open_connection(self.address, self.port)
            writer.write(json.dumps(request).encode("utf-8"))
            writer.write(b"\n")
            await writer.drain()
            response = await reader.readline()
            writer.close()
            await writer.wait_closed()
            return json.loads(response)
        return asyncio.run(communicate())

class Server:

    def __init__(self, address, port):
        self.address = address
        self.port = port

    def start(self):
        async def server():
            await self.before_start()
            asyncio_server = await asyncio.start_server(
                handle_request,
                host=self.address,
                port=self.port
            )
            print(f"listening on port {self.port}")
            sys.stdout.flush()
            async with asyncio_server:
                await asyncio_server.serve_forever()
        async def handle_request(reader, writer):
            request_data = await reader.readline()
            try:
                request = json.loads(request_data)
                assert request["message"] not in ["start", "before_start"]
                if getattr(self, request["message"]):
                    response = await getattr(self, request['message'])(request)
                    response["status"] = "ok"
                else:
                    raise ValueError(f"Unknown message {request['message']}")
            except Exception as e:
                response = {"status": "error", "message": str(e)}
            writer.write(json.dumps(response).encode("utf-8"))
            writer.write(b"\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        asyncio.run(server())
