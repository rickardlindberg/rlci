import asyncio
import json

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
